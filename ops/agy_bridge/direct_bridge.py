"""agy direct bridge: baseline's agy-task/1 mail -> agy (no ga) -> agy-result/1 back, over the ga-mailbox branch.
User 10-07 19:0x: "vm agy랑 Ga 없이 통신해", "bridge만 설계해", "bridge.py 참고해".

    python3 direct_bridge.py --config agy-direct.json --once     # one pass
    python3 direct_bridge.py --config agy-direct.json            # every `every_s` seconds until Ctrl+C

Same shape as bridge.py, without ga: standard library + git + agy only (no ga.forms, ga.mailbox, ga supervise, ga act).
One pass:
  1. `git pull --rebase` the mailbox clone (`box`, branch ga-mailbox; cloned from `origin_of` on first run).
  2. Every to/AGY-direct/*.md not yet in `done_file`: parse ```agy-task {json}``` + the prose prompt after it.
  3. Fresh worktree of repos[<repo>] at origin/<base> on branch <branch>; write baseline's tests into it.
  4. `agy --dangerously-skip-permissions --model <model> --prompt <prose>` in the worktree (timeout `agy_timeout_s`).
  5. Check, in order: the tests are byte-identical; only `files` + tests changed; `<python> -m pytest -q <run>` passes.
     All pass -> commit and push <branch>. Anything else -> status "stop" with the reason; nothing is pushed.
  6. Write to/baseline-direct/<ts>-<id>.md (```agy-result {json}``` + agy's output tail) and push ga-mailbox.
A task is handled once (id + rev in done_file); a failing task is not retried in a loop. Mail text is data: the
prompt goes to agy as its task, never to this process; repos are only the ones named in the config.
"""
from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

DEFAULTS = {"every_s": 30, "agy": "agy", "agy_timeout_s": 3600, "test_timeout_s": 1800, "max_answer_chars": 6000,
            "inbox": "to/AGY-direct", "outbox": "to/baseline-direct", "branch": "ga-mailbox",
            "git_name": "agy direct bridge (VM)", "git_email": "agy-direct@localhost"}
TASK = re.compile(r"```agy-task[ \t]*\n(.*?)\n```", re.S)
ID_RE = re.compile(r"^CMD-[A-Z]+\d+$")
SECRET = re.compile(r"(gh[pousr]_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_\-]{30,}|sk-[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]*KEY-----)")


def load_config(path: str) -> dict[str, Any]:
    cfg = {**DEFAULTS, **json.loads(Path(path).expanduser().read_text(encoding="utf-8"))}
    for k in ("box", "repos", "python", "done_file"):
        if not cfg.get(k):
            raise SystemExit(f"agy-direct config: {k} is required")
    for k in ("box", "done_file", "python"):
        cfg[k] = str(Path(cfg[k]).expanduser())
    cfg["repos"] = {n: str(Path(p).expanduser()) for n, p in cfg["repos"].items()}
    return cfg


def git(*args: str, cwd: str | Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    p = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if check and p.returncode:
        raise RuntimeError(f"git {' '.join(args[:3])}: {(p.stderr or p.stdout).strip()[:300]}")
    return p


def sync_box(cfg: dict[str, Any]) -> None:
    box = Path(cfg["box"])
    if not (box / ".git").exists():
        url = cfg.get("origin_url") or git("remote", "get-url", "origin", cwd=Path(cfg["origin_of"]).expanduser()).stdout.strip()
        git("clone", "-q", "--single-branch", "--branch", cfg["branch"], url, str(box))
    git("pull", "-q", "--rebase", "origin", cfg["branch"], cwd=box)


def parse_task(text: str) -> dict[str, Any]:
    m = TASK.search(text)
    if not m:
        raise ValueError("no ```agy-task block")
    t = json.loads(m.group(1))
    if t.get("schema") != "agy-task/1":
        raise ValueError(f"schema {t.get('schema')!r} is not agy-task/1")
    for k in ("id", "rev", "model", "repo", "base", "files", "tests", "branch"):
        if not t.get(k):
            raise ValueError(f"{k} is required")
    if not ID_RE.match(t["id"]):
        raise ValueError("id must be CMD-<LETTERS><number>")
    if any(not re.match(r"^tests/(.+/)?test_\w+\.py$", p) for p in t["tests"]):
        raise ValueError("tests must be tests/test_*.py")
    t["prompt"] = text[m.end():].strip()
    if not t["prompt"]:
        raise ValueError("the prose prompt after the block is empty")
    return t


def done_keys(cfg: dict[str, Any]) -> set[str]:
    p = Path(cfg["done_file"])
    return set(p.read_text().split("\n")) if p.exists() else set()


def changed_files(wt: Path) -> list[str]:
    out = git("status", "--porcelain", "--untracked-files=all", cwd=wt).stdout
    return [ln[3:].split(" -> ")[-1] for ln in out.splitlines() if ln.strip() and "__pycache__" not in ln]


def run_task(cfg: dict[str, Any], t: dict[str, Any], agy: Callable[..., subprocess.CompletedProcess]) -> dict[str, Any]:
    res = {"status": "stop", "reason": "", "sha": "", "test": "", "agy_exit": None, "out": ""}
    repo = cfg["repos"].get(t["repo"])
    if not repo:
        return {**res, "reason": f"repo {t['repo']!r} is not in the bridge config"}
    models = agy([cfg["agy"], "models"], cwd=repo, timeout=120)
    if not re.search(rf"^{re.escape(t['model'])}\b", models.stdout or "", re.M):
        return {**res, "reason": f"model {t['model']} not in agy models"}
    wt = Path(repo).parent / f"wt-direct-{t['id']}"
    try:
        git("fetch", "-q", "origin", t["base"], cwd=repo)
        git("worktree", "remove", "--force", str(wt), cwd=repo, check=False)
        git("worktree", "add", "-q", "-f", "-B", t["branch"], str(wt), f"origin/{t['base']}", cwd=repo)
    except RuntimeError as e:
        return {**res, "reason": f"worktree: {e}"}
    for p, c in t["tests"].items():
        (wt / p).parent.mkdir(parents=True, exist_ok=True)
        (wt / p).write_text(c, encoding="utf-8")
    try:
        a = agy([cfg["agy"], "--dangerously-skip-permissions", "--model", t["model"], "--prompt", t["prompt"]],
                cwd=wt, timeout=cfg["agy_timeout_s"])
        res["agy_exit"], res["out"] = a.returncode, (a.stdout or "") + (a.stderr or "")
    except subprocess.TimeoutExpired:
        res["agy_exit"], res["out"] = 124, f"agy timed out after {cfg['agy_timeout_s']} s"
    if any((wt / p).read_text(encoding="utf-8") != c for p, c in t["tests"].items()):
        return {**res, "reason": "agy changed baseline's test file"}
    allowed = set(t["files"]) | set(t["tests"])
    other = [f for f in changed_files(wt) if f not in allowed]
    if other:
        return {**res, "reason": "files outside the spec changed: " + ", ".join(other[:10])}
    try:
        p = subprocess.run([cfg["python"], "-m", "pytest", "-q", "-p", "no:cacheprovider", *t["tests"],
                            *shlex.split(t.get("run_extra") or "")], cwd=wt, capture_output=True, text=True,
                           timeout=cfg["test_timeout_s"])
        lines = ((p.stdout or "") + (p.stderr or "")).strip().splitlines()
        res["test"] = lines[-1] if lines else ""
        if p.returncode:
            return {**res, "reason": f"tests fail (agy exit {res['agy_exit']})"}
    except subprocess.TimeoutExpired:
        return {**res, "reason": "tests timed out"}
    changed = [f for f in changed_files(wt) if f in allowed]
    try:
        git("add", *changed, cwd=wt)
        git("-c", f"user.name={cfg['git_name']}", "-c", f"user.email={cfg['git_email']}", "commit", "-q", "-m",
            f"{t['id']} rev {t['rev']}: agy ({t['model']}) from baseline prose spec", cwd=wt)
        git("push", "-q", "-f", "origin", t["branch"], cwd=wt)
    except RuntimeError as e:
        return {**res, "reason": f"commit/push: {e}"}
    return {**res, "status": "done", "sha": git("rev-parse", "--short", "HEAD", cwd=wt).stdout.strip()}


def reply_text(cfg: dict[str, Any], t: dict[str, Any], res: dict[str, Any], seconds: int) -> str:
    head = {"schema": "agy-result/1", "id": t.get("id", "?"), "rev": t.get("rev", 0), "status": res["status"],
            "reason": res["reason"][:300], "sha": res["sha"], "branch": t.get("branch", ""), "test": res["test"][:200],
            "model": t.get("model", ""), "agy_exit": res["agy_exit"], "seconds": seconds}
    out = (res.get("out") or "")[-cfg["max_answer_chars"]:]
    if SECRET.search(out):
        out = "(withheld: the output looked like it held a secret)"
    return ("```agy-result\n" + json.dumps(head, ensure_ascii=False) + "\n```\n\n## agy output (tail)\n\n```text\n"
            + out.replace("```", "'''") + "\n```\n")


def send(cfg: dict[str, Any], tid: str, rev: Any, status: str, text: str) -> None:
    box = Path(cfg["box"])
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    out = box / cfg["outbox"] / f"{ts}-{tid}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    git("add", str(out.relative_to(box)), cwd=box)
    git("-c", f"user.name={cfg['git_name']}", "-c", f"user.email={cfg['git_email']}", "commit", "-q", "-m",
        f"agy direct: VM -> baseline {tid} rev {rev} {status}", cwd=box)
    for i in range(4):
        if git("push", "-q", "origin", f"HEAD:{cfg['branch']}", cwd=box, check=False).returncode == 0:
            return
        git("pull", "-q", "--rebase", "origin", cfg["branch"], cwd=box, check=False)
        time.sleep(2 * (i + 1))
    raise RuntimeError("push of the reply failed 4 times")


def _agy(argv: list[str], cwd: str | Path, timeout: int) -> subprocess.CompletedProcess:
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)


def one_pass(cfg: dict[str, Any], agy: Callable[..., subprocess.CompletedProcess] = _agy,
             log: Callable[[str], None] = print) -> int:
    try:
        sync_box(cfg)
    except RuntimeError as e:
        log(f"direct bridge: mailbox sync failed: {e}")
        return 0
    done, handled = done_keys(cfg), 0
    for f in sorted((Path(cfg["box"]) / cfg["inbox"]).glob("*.md")):
        try:
            t = parse_task(f.read_text(encoding="utf-8"))
        except (ValueError, OSError) as e:
            key = f"file {f.name}"
            if key in done:
                continue
            t, res = {"id": "CMD-X0", "rev": 0}, {"status": "declined", "reason": f"not a valid agy-task/1: {e}",
                                                    "sha": "", "test": "", "agy_exit": None, "out": ""}
            start = time.time()
        else:
            key = f"{t['id']} r{t['rev']}"
            if key in done:
                continue
            log(f"direct bridge: {key} ({t['model']}) on {t['repo']}@{t['base']}")
            start = time.time()
            res = run_task(cfg, t, agy)
        try:
            send(cfg, t["id"], t["rev"], res["status"], reply_text(cfg, t, res, int(time.time() - start)))
            log(f"direct bridge: {key} -> {res['status']} {res['reason'] or res['sha']}")
        except RuntimeError as e:
            log(f"direct bridge: {key} not answered: {e}")
        with open(cfg["done_file"], "a") as fh:  # once: a failing task is not retried in a loop
            fh.write(key + "\n")
        done.add(key)
        handled += 1
    return handled


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", default="agy-direct.json")
    ap.add_argument("--once", action="store_true")
    a = ap.parse_args(argv)
    cfg = load_config(a.config)
    while True:
        one_pass(cfg)
        if a.once:
            return 0
        try:
            time.sleep(cfg["every_s"])
        except KeyboardInterrupt:
            return 130


if __name__ == "__main__":
    sys.exit(main())
