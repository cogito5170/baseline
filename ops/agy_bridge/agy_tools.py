"""Approved tools for the agy bridge (BD-356). ga supervise calls these as Python tools; agy only plans.

Rules for every tool here: read-only, confined to the project folder (the process cwd), output capped, no network,
no shell. A new tool comes in only through baseline review (code + test in test_bridge.py), then reaches every Mac by
the bridge's own `git pull` — never installed because a model asked for it.
"""
from __future__ import annotations

import re
from pathlib import Path

CAP = 20000          # characters returned per call
SKIP = {".git", ".ga", ".ga-supervise", "node_modules", ".venv", "__pycache__"}


def _root() -> Path:
    return Path.cwd().resolve()


def _safe(path: str) -> Path:
    root = _root()
    q = (root / str(path)).resolve()
    if q != root and root not in q.parents:
        raise ValueError("outside the project")
    if any(part in SKIP or part.startswith(".env") for part in q.relative_to(root).parts):
        raise ValueError("not readable through the bridge")
    return q


def list_dir(path: str = ".") -> str:
    """Names in one project folder; folders end with '/'. Hidden and vendored folders are left out."""
    q = _safe(path)
    names = [x.name + ("/" if x.is_dir() else "") for x in q.iterdir() if not x.name.startswith(".") and x.name not in SKIP]
    return "\n".join(sorted(names))[:CAP]


def read_file(path: str, start: int = 1, lines: int = 400) -> str:
    """Lines [start, start+lines) of one text file in the project, numbered."""
    q = _safe(path)
    rows = q.read_text(encoding="utf-8", errors="replace").splitlines()
    s = max(int(start), 1)
    part = rows[s - 1: s - 1 + max(int(lines), 1)]
    return "\n".join(f"{s + i}\t{r}" for i, r in enumerate(part))[:CAP]


def search(pattern: str, path: str = ".", max_hits: int = 50) -> str:
    """Lines matching a regular expression under a project folder: 'file:line: text'."""
    rx = re.compile(pattern)
    base = _safe(path)
    root = _root()
    hits: list[str] = []
    files = [base] if base.is_file() else sorted(base.rglob("*"))
    for f in files:
        rel = f.relative_to(root)
        if not f.is_file() or any(p in SKIP or p.startswith(".") for p in rel.parts) or f.stat().st_size > 2_000_000:
            continue
        try:
            for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                if rx.search(line):
                    hits.append(f"{rel}:{n}: {line.strip()[:200]}")
                    if len(hits) >= int(max_hits):
                        return "\n".join(hits)[:CAP]
        except (UnicodeDecodeError, OSError):
            continue
    return "\n".join(hits)[:CAP] or "(no match)"


DEFAULT_TIMEOUT, MAX_TIMEOUT = 1200, 3600
SUMMARY_LINES = 8
_SECRETISH = re.compile(r"(?i)(key|token|secret|password|credential|auth)")


def run_check(name: str) -> str:
    """Run one command the project owner allowed by name (agy-bridge.json "commands": {"test": ["npm", "test"]},
    or {"test": {"argv": ["npm", "test"], "timeout_s": 1800}} for a slow suite).

    The argv is fixed in the config: the model picks only the name. No shell, project cwd, a time cap (default
    1200 s, at most 3600 s; BD-410: ga-sdk's full suite needs about 600 s), environment variables whose names look
    like secrets removed, output tail capped. Exit code first line.
    """
    import json
    import os
    import subprocess
    allowed = json.loads(os.environ.get("AGY_BRIDGE_COMMANDS") or "{}")
    if name not in allowed:
        raise ValueError(f"not an allowed command: {name!r} (allowed: {', '.join(sorted(allowed)) or 'none'})")
    spec = allowed[name]
    argv, limit = (spec.get("argv"), spec.get("timeout_s", DEFAULT_TIMEOUT)) if isinstance(spec, dict) else (spec, DEFAULT_TIMEOUT)
    if not isinstance(argv, list) or not argv or not all(isinstance(a, str) for a in argv):
        raise ValueError(f"command {name!r}: argv must be a non-empty list of strings")
    limit = max(1, min(int(limit), MAX_TIMEOUT))
    env = {k: v for k, v in os.environ.items() if not _SECRETISH.search(k)}
    try:
        p = subprocess.run(list(argv), cwd=_root(), env=env, capture_output=True, text=True, timeout=limit)
        out, code = (p.stdout or "") + (p.stderr or ""), p.returncode
    except subprocess.TimeoutExpired:
        out, code = f"timed out after {limit} s", 124
    lines = out.rstrip().splitlines()
    summary = "\n".join(lines[-SUMMARY_LINES:])
    failing = [ln for ln in lines if re.match(r"^(FAIL|ERROR):|^\s*(✘|×)\s", ln)][:60]
    # Previews may keep only the head or only the tail of a result, so the summary (counts) and the failing test names
    # sit at both ends (BD-413/414: AG7 lost the count at the head, AG8 lost the names in the middle).
    key = f"--- failing ({len(failing)}) ---\n" + "\n".join(failing) + \
        f"\n--- last {min(len(lines), SUMMARY_LINES)} lines ---\n{summary}"
    return f"exit {code}\n{key}\n--- output tail ---\n" + out[-(CAP // 2):] + f"\n--- again ---\nexit {code}\n{key}\n"
