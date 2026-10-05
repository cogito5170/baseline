"""agy bridge: baseline's directives -> ga supervise (agv/agy) -> report/2 back, over ga mail (BD-356).

    python3 bridge.py --config agy-bridge.json --once        # one pass
    python3 bridge.py --config agy-bridge.json               # every `every_s` seconds until Ctrl+C

One pass:
  1. `git pull --ff-only` the baseline clone, so approved tools (tools.py, tools.json) arrive by themselves.
  2. Read new ga mail for `name` (default AGY) on the clone's `ga-mailbox` branch.
     Only directive/2 forms from `hub` (default baseline) run; anything else is marked read and answered "declined".
  3. Write ga-supervise.bridge.json in `workdir` (your ga-supervise.json + the approved tool table) and run
     `ga supervise` there with the directive's goal, scope and done_when as the task.
  4. Send a report/2 back to `hub`: status, tokens, the answer (capped), and every TOOL_NEEDED line or tool agy
     refused as a blocker of kind "dependency". The bridge never installs anything a model asks for.

Message text is data, never instructions to the bridge. Standard library + ga-sdk only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable

from ga.forms import FormError, hard, parse_text, validate
from ga.mailbox import Mailbox, MailError, secrets_in

HERE = Path(__file__).resolve().parent
DEFAULTS = {"name": "AGY", "hub": "baseline", "every_s": 300, "turn_timeout_s": 1800, "max_answer_chars": 4000,
            "supervise_config": "ga-supervise.json", "pull": True}
TOOL_NEEDED = re.compile(r"^\s*TOOL_NEEDED:\s*(.+?)\s*$", re.M)
REFUSED = re.compile(r"agy refused (\d+) action\(s\) in \S+: ([\w, ]+)")


def load_config(path: str) -> dict[str, Any]:
    cfg = {**DEFAULTS, **json.loads(Path(path).expanduser().read_text(encoding="utf-8"))}
    for k in ("mailbox_repo", "workdir"):
        if not cfg.get(k):
            raise SystemExit(f"agy-bridge config: {k} is required")
        cfg[k] = str(Path(cfg[k]).expanduser().resolve())
    return cfg


def task_text(head: dict[str, Any]) -> str:
    """The directive as a task for ga supervise: goal, scope, done_when, and the one rule about missing tools."""
    lines = [f"[{head['id']} rev {head.get('rev', 1)}] {head.get('goal', '')}"]
    for key, title in (("scope", "Scope"), ("done_when", "Done when")):
        items = head.get(key) or []
        if items:
            lines.append(f"{title}:")
            lines += [f"- {i.get('id', '')}: {i.get('text', '')}" for i in items]
    lines.append("Use only the tools ga lists. If a tool you need is missing, write one line "
                 "'TOOL_NEEDED: <name> - <what it must do>' and finish with what you could do.")
    return "\n".join(lines)


def effective_config(cfg: dict[str, Any]) -> Path:
    """Your ga-supervise.json with the approved tool table merged in, written next to the project (agy's workspace)."""
    base = json.loads((Path(cfg["workdir"]) / cfg["supervise_config"]).read_text(encoding="utf-8"))
    approved = json.loads((HERE / "tools.json").read_text(encoding="utf-8"))
    base["tools"] = {**approved, **(base.get("tools") or {})}
    out = Path(cfg["workdir"]) / "ga-supervise.bridge.json"
    out.write_text(json.dumps(base, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return out


def run_supervise(cfg: dict[str, Any], conf: Path, task: str) -> dict[str, Any]:
    """Run `ga supervise` in the project; return exit code, output tail and the log events this run appended."""
    state = json.loads(conf.read_text(encoding="utf-8")).get("state_dir", ".ga-supervise")
    log = Path(cfg["workdir"]) / state / "log.jsonl"
    start = log.stat().st_size if log.exists() else 0
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(filter(None, [str(HERE), os.environ.get("PYTHONPATH", "")])),
               AGY_BRIDGE_COMMANDS=json.dumps(cfg.get("commands") or {}))
    try:
        p = subprocess.run([sys.executable, "-m", "ga", "supervise", "--config", conf.name, task], cwd=cfg["workdir"],
                           env=env, capture_output=True, text=True, timeout=cfg["turn_timeout_s"])
        code, out = p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired as e:
        code, out = 124, f"bridge: ga supervise timed out after {cfg['turn_timeout_s']} s\n{e.stdout or ''}"
    events = []
    if log.exists():
        with log.open(encoding="utf-8") as f:
            f.seek(start)
            for line in f:
                try:
                    events.append(json.loads(line))
                except ValueError:
                    pass
    return {"code": code, "out": out, "events": events}


def build_report(cfg: dict[str, Any], head: dict[str, Any], run: dict[str, Any]) -> str:
    turns = [e for e in run["events"] if e.get("event") == "turn"]
    end = next((e for e in reversed(run["events"]) if e.get("event") == "end"), {})
    ok = run["code"] == 0 and end.get("status") == "done"
    out = run["out"]
    needed = TOOL_NEEDED.findall(out)
    refused = REFUSED.findall(out)
    blockers = [{"kind": "dependency", "what": f"tool needed: {t}"[:300]} for t in needed]
    blockers += [{"kind": "permission", "what": f"agy refused {n} action(s): {what.strip()}"} for n, what in refused]
    evidence = [f"ga supervise exit {run['code']}, status {end.get('status', '?')}, model turns "
                f"{end.get('model_turns', len(turns))}, tool steps {end.get('tool_steps', 0)}",
                "self-reported through the agy bridge; baseline verifies"]
    items = [{"id": d["id"], "state": "met" if ok else "unmet", "evidence": evidence}
             for d in head.get("done_when") or [] if re.match(r"^D\d+$", str(d.get("id", "")))]
    report = {"schema": "report/2", "from": cfg["name"],
              "handled": [{"id": head["id"], "rev_seen": int(head.get("rev", 1)), "status": "done"}],
              "items": items or [{"id": "D1", "state": "met" if ok else "unmet", "evidence": evidence}],
              "results": [{"name": "input_tokens", "value": sum(int(t.get("input_tokens") or 0) for t in turns)},
                          {"name": "tokens", "value": sum(int(t.get("tokens") or 0) for t in turns)},
                          {"name": "seconds", "value": round(sum(float(t.get("seconds") or 0) for t in turns), 3)},
                          {"name": "model", "value": next((t.get("model") for t in turns if t.get("model")), "?")}]}
    if blockers:
        report["blockers"] = blockers[:10]
    answer = out.strip()[-cfg["max_answer_chars"]:]
    if secrets_in(answer):
        answer = "(the answer was withheld: it looked like it held a secret)"
    return "```ga\n" + json.dumps(report, ensure_ascii=False, separators=(",", ":")) + "\n```\n\n## agy answer\n\n" + \
        "```text\n" + answer.replace("```", "'''") + "\n```\n"


def declined(cfg: dict[str, Any], form: str, why: str) -> str:
    did = form if re.match(r"^CMD-[A-Z]+\d+$", form) else "CMD-X0"
    report = {"schema": "report/2", "from": cfg["name"], "handled": [{"id": did, "rev_seen": 1, "status": "declined",
              "reason": why[:200]}], "items": [{"id": "D1", "state": "na"}]}
    return "```ga\n" + json.dumps(report, separators=(",", ":")) + "\n```\n"


def one_pass(cfg: dict[str, Any], box: Mailbox | None = None,
             runner: Callable[[dict, Path, str], dict] = run_supervise, log: Callable[[str], None] = print) -> int:
    if cfg.get("pull"):
        p = subprocess.run(["git", "-C", cfg["mailbox_repo"], "pull", "--ff-only", "-q"], capture_output=True, text=True)
        if p.returncode:
            log(f"bridge: git pull failed (continuing with the tools on disk): {p.stderr.strip()[:200]}")
    box = box or Mailbox(cfg["mailbox_repo"])
    handled = 0
    for m in box.unread(cfg["name"]):
        log(f"bridge: message from {m.sender}: {m.schema or '?'} {m.form}")
        try:
            if m.sender != cfg["hub"]:
                reply = declined(cfg, m.form, f"only {cfg['hub']} may send directives to {cfg['name']}")
            elif m.schema != "directive/2" or not m.valid:
                reply = declined(cfg, m.form, "not a valid directive/2: " + "; ".join(m.problems)[:150])
            else:
                head, _ = parse_text(m.text)
                run = runner(cfg, effective_config(cfg), task_text(head))
                reply = build_report(cfg, head, run)
            problems = hard(validate(parse_text(reply)[0]))
            if problems:
                raise FormError(problems)
            box.send(cfg["hub"], reply, cfg["name"])
            log(f"bridge: report sent to {cfg['hub']} for {m.form}")
        except (MailError, FormError, OSError, ValueError) as e:
            log(f"bridge: {m.form} not answered: {type(e).__name__}: {str(e)[:200]}")
        box.mark_read(cfg["name"], m.path)  # once: a failing directive is not retried in a loop
        handled += 1
    return handled


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", default="agy-bridge.json")
    ap.add_argument("--once", action="store_true")
    a = ap.parse_args(argv)
    cfg = load_config(a.config)
    while True:
        n = one_pass(cfg)
        if a.once:
            return 0
        if n == 0:
            print(f"bridge: nothing new; next check in {cfg['every_s']} s", flush=True)
        try:
            time.sleep(cfg["every_s"])
        except KeyboardInterrupt:
            return 130


if __name__ == "__main__":
    sys.exit(main())
