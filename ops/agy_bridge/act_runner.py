"""Code work through the agy bridge (BD-424): a directive with an item file runs `ga act` instead of `ga supervise`.

baseline writes `items/<directive id>.json` in this folder (it reaches the Mac by the bridge's own git pull):

    {"item":     {"id": "CMD-AGA1", "goal": "...", "files": ["backend/app/worker/__main__.py"], "done_when": "test"},
     "tests":    {"backend/tests/test_worker_banner.py": "<file text>"},   # acceptance tests baseline wrote
     "commands": {"commands": {"test": ["{venv_python}", "-m", "unittest", ...]}, "timeout_s": 600},
     "base":     "claude/gracious-meitner-vp49xe",                          # the branch to start from
     "rewrite":  ["backend/app/worker/__main__.py"]}                       # optional: removed in the worktree first

One run, all in a separate git worktree next to the user's checkout (their running servers and edits are untouched):
  1. `git fetch origin <base>`, `git worktree add -B agv/<id> <dir> origin/<base>`;
  2. node_modules of the checkout's frontend/ is linked in, so test commands run;
  3. baseline's tests are written; the model may not edit them (they are not in the item's files); files listed in
     "rewrite" (each one of the item's files) are removed so the model writes them whole with NEW (BD-450);
  4. `python -m ga act --item ... --repo <worktree> --backend/--model/--options from the bridge config`;
  5. the change is committed on agv/<id> (local only) and returned as a patch (capped; withheld if secret-looking).
Placeholders in command argv: {venv_python} = the checkout's .venv python, {checkout} = the user's checkout.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

from ga.mailbox import secrets_in

HERE = Path(__file__).resolve().parent
PATCH_CAP = 60_000
SAFE_PATH = re.compile(r"^(?!/)(?!.*\.\.)[\w./@()\[\]-]+$")


def item_file(directive_id: str) -> Path:
    return HERE / "items" / f"{directive_id}.json"


def _git(repo: Path, *a: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True, check=check)


def _expand(argv: list[str], subs: dict[str, str]) -> list[str]:
    out = []
    for x in argv:
        for k, v in subs.items():
            x = x.replace("{" + k + "}", v)
        out.append(x)
    return out


def prepare(spec: dict[str, Any], checkout: Path, did: str) -> Path:
    """The worktree for one item, from origin/<base>, with baseline's tests in it. Raises ValueError on a bad spec."""
    base = spec.get("base") or "claude/gracious-meitner-vp49xe"
    if not re.match(r"^[\w./-]+$", base):
        raise ValueError("bad base branch name")
    for rel in spec.get("tests") or {}:
        if not SAFE_PATH.match(rel) or rel.split("/")[0] in (".git", ".ga") or rel.startswith(".env"):
            raise ValueError(f"bad test path: {rel}")
    owned = list((spec.get("item") or {}).get("files") or [])
    for rel in spec.get("rewrite") or []:
        if not SAFE_PATH.match(rel) or rel not in owned:
            raise ValueError(f"bad rewrite path (must be one of the item's files): {rel}")
    _git(checkout, "fetch", "-q", "origin", base)
    wt = checkout.parent / f"{checkout.name}-agv-{did}"
    if wt.exists():
        _git(checkout, "worktree", "remove", "--force", str(wt), check=False)
    _git(checkout, "worktree", "add", "-q", "-B", f"agv/{did}", str(wt), f"origin/{base}")
    nm = checkout / "frontend" / "node_modules"
    if nm.is_dir() and (wt / "frontend").is_dir() and not (wt / "frontend" / "node_modules").exists():
        os.symlink(nm, wt / "frontend" / "node_modules")
    for rel, text in (spec.get("tests") or {}).items():
        p = wt / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    for rel in spec.get("rewrite") or []:  # BD-450: a small model writes the whole file (NEW) instead of exact EDIT blocks
        p = wt / rel
        if p.is_file() and not p.is_symlink():
            p.unlink()
    return wt


MODEL_SLUG = re.compile(r"^[a-z0-9][a-z0-9.-]{1,60}$")  # agent names
# the slugs `agy models` lists on the user's account (VM, 2026-10-06); an item may name only one of these
MODELS = frozenset({
    "gemini-3.8-flash-high", "gemini-3.8-flash-medium", "gemini-3.8-flash-low",
    "gemini-3.7-flash-high", "gemini-3.7-flash-medium", "gemini-3.7-flash-low",
    "gemini-3.6-flash-high", "gemini-3.6-flash-medium", "gemini-3.6-flash-low",
    "gemini-3.1-pro-high", "gemini-3.1-pro-low",
    "claude-opus-5-5-low", "claude-opus-5-5-medium", "claude-opus-5-5-high",
    "claude-sonnet-5-5-low", "claude-sonnet-5-5-medium", "claude-sonnet-5-5-high",
    "gpt-oss-120b-medium"})

def run_act(cfg: dict[str, Any], spec: dict[str, Any], wt: Path, checkout: Path) -> dict[str, Any]:
    """`ga act` in the worktree; returns {code, out, result (act/1 dict or None)}."""
    act = cfg.get("act") or {}
    subs = {"venv_python": str(checkout / ".venv" / "bin" / "python"), "checkout": str(checkout)}
    cmds = dict(spec.get("commands") or {})
    cmds["commands"] = {k: _expand(v, subs) for k, v in (cmds.get("commands") or {}).items()}
    tmp = Path(tempfile.mkdtemp(prefix="agv-act-"))
    (tmp / "item.json").write_text(json.dumps(spec["item"], ensure_ascii=False), encoding="utf-8")
    (tmp / "commands.json").write_text(json.dumps(cmds, ensure_ascii=False), encoding="utf-8")
    argv = [sys.executable, "-m", "ga", "act", "--item", str(tmp / "item.json"), "--repo", str(wt),
            "--backend", act.get("backend", "agv"), "--model", act.get("model", "gpt-oss-120b-medium"),
            "--options", json.dumps(act.get("options") or {}), "--config", str(tmp / "commands.json"),
            "--state", str(tmp / "state"), "--max-turns", str(int(act.get("max_turns", 10)))]
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=int(act.get("timeout_s", 3600)))
        code, out = p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        code, out = 124, "ga act timed out"
    result = None
    for line in reversed(out.strip().splitlines()):
        try:
            result = json.loads(line)
            break
        except ValueError:
            continue
    return {"code": code, "out": out, "result": result}


def finish(wt: Path, checkout: Path, did: str, owned: list[str]) -> str:
    """Commit the model's change on agv/<id> (baseline's tests excluded from 'changed') and return the patch."""
    _git(wt, "add", "-A")
    _git(wt, "reset", "-q", "--", "frontend/node_modules", check=False)  # the link prepare() made is not a change (BD-427)
    if not _git(wt, "status", "--porcelain").stdout.strip():
        patch = ""
    else:
        _git(wt, "-c", "user.name=agv", "-c", "user.email=agv@localhost", "commit", "-q", "-m", f"{did}: agv ga act")
        patch = _git(wt, "format-patch", "-1", "--stdout").stdout
    _git(checkout, "worktree", "remove", "--force", str(wt), check=False)
    if secrets_in(patch):
        return "(the patch was withheld: it looked like it held a secret)"
    return patch if len(patch) <= PATCH_CAP else patch[:PATCH_CAP] + "\n(patch cut at the cap)\n"


def report(cfg: dict[str, Any], head: dict[str, Any], run: dict[str, Any], patch: str,
           commit: dict[str, str] | None = None) -> str:
    res = run.get("result") or {}
    ok = run["code"] == 0 and res.get("status") == "done"
    tok = res.get("tokens") or {}
    ev = [f"ga act exit {run['code']}, status {res.get('status', '?')}: {str(res.get('reason', ''))[:160]}",
          f"turns {res.get('turns', '?')}, changed {', '.join(res.get('changed') or []) or 'nothing'}",
          "self-reported through the agy bridge; baseline verifies the patch"]
    items = [{"id": d["id"], "state": "met" if ok else "unmet", "evidence": ev}
             for d in head.get("done_when") or [] if re.match(r"^D\d+$", str(d.get("id", "")))]
    rep = {"schema": "report/2", "from": cfg["name"],
           "handled": [{"id": head["id"], "rev_seen": int(head.get("rev", 1)), "status": "done"}],
           "items": items or [{"id": "D1", "state": "met" if ok else "unmet", "evidence": ev}],
           "results": [{"name": "input_tokens", "value": int(tok.get("input") or 0)},
                       {"name": "tokens", "value": int(tok.get("total") or 0)},
                       {"name": "turns", "value": int(res.get("turns") or 0)},
                       {"name": "model", "value": (cfg.get("act") or {}).get("model", "?")}]}
    if commit:
        rep["commits"] = [commit]
        rep["change_size"] = "implementation"
    if not ok:
        rep["blockers"] = [{"kind": "dependency", "what": f"ga act: {str(res.get('reason') or run['out'][-200:])}"[:300]}]
    tail = run["out"].strip()[-3000:]
    if secrets_in(tail):
        tail = "(withheld: looked like it held a secret)"
    body = "```ga\n" + json.dumps(rep, ensure_ascii=False, separators=(",", ":")) + "\n```\n\n## ga act result\n\n```text\n" + \
        tail.replace("```", "'''") + "\n```\n"
    if patch:
        body += "\n## patch\n\n```diff\n" + patch.replace("```", "'''") + "\n```\n"
    return body


def handle(cfg: dict[str, Any], head: dict[str, Any],
           runner: Callable[[dict, dict, Path, Path], dict] = run_act, spec: dict[str, Any] | None = None) -> str:
    spec = spec or json.loads(item_file(head["id"]).read_text(encoding="utf-8"))
    if spec.get("model"):  # BD-455: baseline picks the model per item (agy slugs: gpt-oss, gemini, claude)
        if spec["model"] not in MODELS:
            raise ValueError(f"unknown model (not in `agy models`): {spec['model']!r}")
        cfg = {**cfg, "act": {**(cfg.get("act") or {}), "model": spec["model"]}}
    if "agent" in spec:  # the agy plugin agent for this item ("" = agy's default agent)
        if spec["agent"] and not MODEL_SLUG.match(str(spec["agent"])):
            raise ValueError(f"bad agent name: {spec['agent']!r}")
        act = cfg.get("act") or {}
        opts = {k: v for k, v in (act.get("options") or {}).items() if k != "agent"}
        cfg = {**cfg, "act": {**act, "options": {**opts, **({"agent": spec["agent"]} if spec["agent"] else {})}}}
    checkout = Path((cfg.get("act") or {}).get("repo") or "").expanduser().resolve()
    if not (checkout / ".git").exists():
        raise ValueError(f"act.repo is not a git checkout: {checkout}")
    wt = prepare(spec, checkout, head["id"])
    run = runner(cfg, spec, wt, checkout)
    patch = finish(wt, checkout, head["id"], spec["item"].get("files") or [])
    commit = publish(cfg, checkout, head, patch)
    return report(cfg, head, run, patch, commit)


def publish(cfg: dict[str, Any], checkout: Path, head: dict[str, Any], patch: str) -> dict[str, str] | None:
    """BD-457: push the agv commit as agv/<id>-r<rev> so the report can name it and ga judge / the GA hub can judge it
    (a fresh clone of that sha). Only a real patch that passed the secret check is pushed; never with force."""
    act = cfg.get("act") or {}
    if not act.get("push", True) or not patch.startswith("From ") or "withheld" in patch[:200]:
        return None
    did, rev = head["id"], int(head.get("rev", 1))
    sha = _git(checkout, "rev-parse", f"agv/{did}", check=False).stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        return None
    branch = f"agv/{did}-r{rev}"
    p = _git(checkout, "push", "-q", act.get("remote", "origin"), f"{sha}:refs/heads/{branch}", check=False)
    if p.returncode != 0:
        return None
    return {"repo": act.get("repo_name", "cogito5170/Token"), "branch": branch, "sha": sha}
