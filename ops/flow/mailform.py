"""Baseline-side directive/2 classifier (user 10-07 18:2x: "VM에 보내는 spec 정보 field가 달라서 생기는 문제 -거절 등-
이 절대 생기지 않도록 baseline에서 보내는 정보를 format에 맞게 분류해주는 분류기 ... VM쪽이 아니라 baseline쪽에서 처리해").

Every to/AGY mail is built here; nothing hand-assembles a head any more. ``build(info)`` takes whatever baseline knows
(any key names from ALIASES), sorts each value into the field the VM bridge expects, fills what the form requires,
drops what the form does not know (listed back, never sent), and refuses locally (FormError) only what it cannot
repair. The result always passes ops/flow/mailcheck.py (every rule the VM has declined for) and ops/flow/nocode.py.

Field sets are the ones the VM has accepted (99 directive/2 mails, ga-mailbox to/AGY, 10-06..10-07):
  head    schema id rev to after goal why scope done_when budget model changes
  ga-act  item{id goal files done_when} tests commands{commands timeout_s} base repo

    from mailform import build, write
    text, head, notes = build({"id": "CMD-ACTB1", "title": ..., "goal": ..., "files": [...], "test": path, ...})
    write(mailbox_worktree, text, head)           # to/AGY/<ts>-baseline-<id>.md, after the checks

    python3 ops/flow/mailform.py --self-test
"""
from __future__ import annotations

import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import mailcheck  # noqa: E402
import nocode  # noqa: E402

GOAL_HEAD_MAX = 1800
DEFAULT_MODEL = "gemini-3.1-pro-high"  # policy spec_split.strong_vm_worker_1007 (code work)
DEFAULT_BASE = "vm/G4-INT"
DEFAULT_REPO = "ga-sdk"
DEFAULT_TIMEOUT_S = 900

# input key -> canonical key. Anything not here is dropped (reported in notes), never sent.
ALIASES = {
    "id": "id", "cmd": "id", "name": "id",
    "rev": "rev", "revision": "rev",
    "title": "title", "summary": "title",
    "goal": "goal", "spec": "goal", "what": "goal", "task": "goal",
    "why": "why", "reason": "why", "because": "why",
    "files": "files", "file": "files", "paths": "files",
    "test": "tests", "tests": "tests",
    "guards": "guards", "guard_tests": "guards",
    "deselect": "deselect",
    "model": "model",
    "base": "base", "branch": "base",
    "repo": "repo",
    "changes": "changes", "change": "changes", "what_changed": "changes",
    "done_when": "done_when", "done": "done_when",
    "scope": "scope",
    "after": "after", "depends_on": "after",
    "timeout_s": "timeout_s",
    "read_only": "read_only",
    "to": "to", "recipient": "to",
    "from": "from", "sender": "from",
    "probe": "probe", "probes": "probe",
}


class FormError(ValueError):
    """Baseline must fix this before anything is sent (it cannot be repaired without guessing)."""


def _id(raw) -> str:
    s = re.sub(r"[^A-Z0-9]", "", str(raw or "").upper().removeprefix("CMD-").removeprefix("CMD"))
    m = re.fullmatch(r"([A-Z]+)(\d+)", s)
    if not m:  # letters and digits mixed (e.g. G2C1 -> prefix G, number 2, then C1): keep letters, then all digits
        letters, digits = "".join(c for c in s if c.isalpha()), "".join(c for c in s if c.isdigit())
        if not letters or not digits:
            raise FormError(f"id {raw!r}: need letters and a number, e.g. CMD-ACTB1")
        s = letters + digits
    return "CMD-" + s


def _list(v) -> list:
    if v is None or v == "":
        return []
    return list(v) if isinstance(v, (list, tuple)) else [v]


def _items(v, prefix: str) -> list[dict]:
    out = []
    for i, x in enumerate(_list(v), 1):
        if isinstance(x, dict) and x.get("text"):
            out.append({"id": str(x.get("id") or f"{prefix}{i}"), "text": str(x["text"])})
        elif str(x).strip():
            out.append({"id": f"{prefix}{i}", "text": str(x)})
    return out


def _tests(v) -> dict[str, str]:
    """tests: a path, a list of paths, or {repo path: content}. Paths are read here; the repo path is tests/<name>."""
    if isinstance(v, dict):
        return {(k if k.startswith("tests/") else f"tests/{Path(k).name}"): str(c) for k, c in v.items()}
    out = {}
    for p in _list(v):
        p = Path(p)
        if not p.is_file():
            raise FormError(f"test file {p} not found")
        out[f"tests/{p.name}"] = p.read_text(encoding="utf-8")
    return out


def classify(info: dict) -> tuple[dict, list[str]]:
    """Sort input keys into canonical ones. Returns (canonical dict, notes about dropped / merged keys)."""
    c, notes = {}, []
    for k, v in info.items():
        key = ALIASES.get(str(k).lower().strip())
        if key is None:
            notes.append(f"dropped {k!r}: the VM form has no such field")
        elif key in c and c[key] != v:
            notes.append(f"{k!r} -> {key}: already set, kept the first value")
        else:
            c[key] = v
    return c, notes


def build(info: dict) -> tuple[str, dict, list[str]]:
    c, notes = classify(info)
    did = _id(c.get("id"))
    if did != str(c.get("id")):
        notes.append(f"id {c.get('id')!r} -> {did}")
    rev = c.get("rev", 1)
    try:
        rev = int(rev)
    except (TypeError, ValueError):
        raise FormError(f"rev {rev!r} is not a number")
    if rev < 1:
        raise FormError("rev must be >= 1")
    title, goal = str(c.get("title") or "").strip(), str(c.get("goal") or "").strip()
    if not goal and not title:
        raise FormError("goal: nothing to send (give goal or title)")
    files = [str(f) for f in _list(c.get("files"))]
    tests = _tests(c.get("tests")) if c.get("tests") else {}
    code_work = bool(files) and not c.get("read_only")
    if files and not tests and not c.get("read_only"):
        raise FormError("code work needs baseline's acceptance test (tests=...) or read_only=True")
    why = str(c.get("why") or "").strip() or f"baseline: {title or goal[:120]}"
    if not c.get("why"):
        notes.append("why was missing: filled from the title")
    scope = _items(c.get("scope"), "S") or [{"id": "S1", "text": ("only " + ", ".join(files) + " in a "
                                             f"{c.get('repo') or DEFAULT_REPO} worktree; the tests are baseline's")
                                             if files else "read only: change nothing"}]
    test_names = ", ".join(tests) or "the checks"
    done = _items(c.get("done_when"), "D") or [{"id": "D1", "text": (
        f"ga act ends done: {test_names} and the guard tests pass; the report carries the pushed agv commit"
        if code_work else f"the report answers the goal; {test_names} reported")}]
    to = str(c.get("to") or "LOCAL")  # policy direct_pipeline_1007: the VM dispatcher
    if not re.fullmatch(r"[A-Za-z][\w-]*", to):
        raise FormError(f"to {to!r}: a mailbox name like AGY or LOCAL")
    head = {"schema": "directive/2", "id": did, "rev": rev, "to": to, "after": [str(a) for a in _list(c.get("after"))],
            "goal": (f"{title}: {goal}" if title and goal else title or goal)[:GOAL_HEAD_MAX], "why": why,
            "scope": scope, "done_when": done, "budget": {"claude_p_runs": 0},
            "model": str(c.get("model") or DEFAULT_MODEL)}
    if c.get("from"):  # issue/1: the Claude side that sent it (baseline / QA)
        head["from"] = str(c["from"])
    if c.get("probe"):  # issue/1 fast path: named probes the bridge runs itself, no model
        head["probe"] = [str(p) for p in _list(c["probe"])]
    if to != "AGY":  # the model field is for the VM bridge only (it picks the agy model)
        head.pop("model")
    elif head["model"] not in mailcheck.KNOWN_MODELS:
        raise FormError(f"model {head['model']!r} not in mailcheck.KNOWN_MODELS (the VM would decline it); add it "
                        "there once the VM lists it")
    if rev > 1:
        ch = c.get("changes")
        if isinstance(ch, str) or (ch and not isinstance(ch, list)):
            ch = [ch]
        fixed = []
        for x in ch or []:
            if isinstance(x, dict) and x.get("text"):
                fixed.append({"item": str(x.get("item") or done[0]["id"]),
                              "op": x.get("op") if x.get("op") in mailcheck.CHANGE_OPS else "edit", "text": str(x["text"])})
            elif str(x).strip():
                fixed.append({"item": done[0]["id"], "op": "edit", "text": str(x)})
        if not fixed:
            raise FormError(f"rev {rev}: say what changed (changes=...) — the VM requires it")
        head["changes"] = fixed
    elif c.get("changes"):
        notes.append("changes dropped: rev 1 has nothing to change")
    text = "```ga\n" + json.dumps(head, ensure_ascii=False) + "\n```\n"
    if code_work:
        guards, desel = [str(g) for g in _list(c.get("guards"))], [str(d) for d in _list(c.get("deselect"))]
        spec = {"item": {"id": did, "goal": goal or title, "files": files, "done_when": "test"}, "tests": tests,
                "commands": {"commands": {"test": ["{python}", "-m", "pytest", "-q", "-p", "no:cacheprovider", *tests,
                                                   *guards, *[x for d in desel for x in ("--deselect", d)]]},
                             "timeout_s": int(c.get("timeout_s") or DEFAULT_TIMEOUT_S)},
                "base": str(c.get("base") or DEFAULT_BASE), "repo": str(c.get("repo") or DEFAULT_REPO)}
        text += "\n```ga-act\n" + json.dumps(spec, ensure_ascii=False) + "\n```\n"
    hard, warn = mailcheck.problems(text)
    if hard:  # a bug in this classifier, not in the caller's input
        raise FormError("classifier produced an invalid mail: " + "; ".join(hard))
    nocode.check_mail(text)
    return text, head, notes + warn


def write(box: Path, text: str, head: dict) -> Path:
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    out = Path(box) / "to" / head["to"] / f"{ts}-baseline-{head['id']}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return out


def self_test() -> None:
    import tempfile
    t = Path(tempfile.mkdtemp()) / "test_x.py"
    t.write_text("import unittest\n")
    # every past decline, given as baseline might write it, comes out valid
    cases = {
        "dashed id (G2C1)": {"id": "CMD-G2-C1", "goal": "g", "why": "w"},
        "lower-case, no CMD": {"id": "actb1", "goal": "g", "why": "w"},
        "no why (PING6)": {"id": "CMD-PING6", "goal": "g"},
        "rev 2 with a plain note (TKG13, ACT1)": {"id": "CMD-ACTB1", "rev": 2, "goal": "g", "why": "w",
                                                  "changes": "model gemini-3.1-pro-high", "files": ["a.py"], "test": t},
        "old head keys (X0)": {"id": "CMD-X1", "kind": "directive", "from": "baseline", "ref": "x", "goal": "g"},
        "aliases": {"cmd": "CMD-Q1", "spec": "g", "reason": "w", "paths": "a.py", "tests": [t], "branch": "vm/X"},
        "read only": {"id": "CMD-GCK9", "goal": "check", "why": "w", "read_only": True},
    }
    for name, info in cases.items():
        text, head, notes = build(info)
        assert mailcheck.problems(text)[0] == [], name
    _, h, notes = build(cases["old head keys (X0)"])
    assert set(h) <= mailcheck.KNOWN and any("dropped 'kind'" in n for n in notes)
    assert build(cases["dashed id (G2C1)"])[1]["id"] == "CMD-GC21"
    assert build(cases["rev 2 with a plain note (TKG13, ACT1)"])[1]["changes"][0]["op"] == "edit"
    for name, info in {"rev 2 without changes": {"id": "CMD-A1", "rev": 2, "goal": "g"},
                       "code work without a test (GCK2-like)": {"id": "CMD-A1", "goal": "g", "files": ["a.py"]},
                       "unknown model (VB3)": {"id": "CMD-A1", "goal": "g", "model": "gemini-9-ultra", "to": "AGY"},
                       "no goal": {"id": "CMD-A1"}, "no number": {"id": "CMD-ABC", "goal": "g"}}.items():
        try:
            build(info)
        except FormError:
            continue
        raise AssertionError(f"{name}: should be refused locally")
    print("mailform self-test OK")


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        self_test()
    else:
        print(__doc__)
