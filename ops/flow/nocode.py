"""No code from baseline (policy.json spec_split.no_code_from_baseline, user 10-07 17:2x "기록도 하고 코드적으로 막아주라").

Every directive baseline mails to the VM (to/AGY/*.md) and every spec/1 baseline sends through flow.py must be WHAT
only: rules, file and function names, wire-form fields, and baseline's acceptance test. This module rejects:
  - ga act action blocks (EDIT/NEW/RUN/NEED lines, SEARCH/REPLACE markers, <<<<<<< ======= >>>>>>> markers)
  - fenced code inside the goal or any other text field
  - code-like lines (def/class/import/return/assignments/decorators ...) beyond a small allowance for inline names
  - a ga-act block carrying anything in "tests" other than tests/test_*.py files (the acceptance tests) and the
    wire-form registry ga/forms/registry.json (JSON data = spec), or a "rewrite"/"actions" key
  - an over-long goal (a prose spec fits in GOAL_MAX characters)
The acceptance test files themselves are the one place baseline writes code (policy: baseline's tests).

    python3 ops/flow/nocode.py <mail.md ...>    -> exit 1 and the reasons when any mail carries code
    python3 ops/flow/nocode.py --self-test
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

GOAL_MAX = 2500
CODE_LINES_MAX = 2  # lines that look like code, allowed in prose (e.g. a quoted signature)
ACTION = re.compile(r"^\s*(EDIT|NEW|RUN|NEED)\s+\S", re.M)
MARKERS = re.compile(r"^\s*(<{7}|={7}|>{7}|SEARCH\s*$|REPLACE\s*$|@@ .* @@|\+\+\+ |--- a/)", re.M)
FENCE = re.compile(r"```")
CODE_LINE = re.compile(r"^\s*(def |class |import |from \S+ import |return\b|@\w|if __name__|for \w+ in .*:$|"
                       r"while .*:$|try:$|except\b.*:$|[A-Za-z_][\w.\[\]'\"]*\s*(=|\+=|-=)\s*\S)", re.M)
BLOCK = re.compile(r"```(ga|ga-act)[ \t]*\n(.*?)\n```", re.S)
TEST_PATH = re.compile(r"^tests/(.+/)?test_[\w]+\.py$")
SPEC_DATA = {"ga/forms/registry.json"}  # wire-form definitions are spec (policy: wire-form fields); must be JSON


class CodeFound(ValueError):
    pass


def text_problems(where: str, text: str) -> list[str]:
    """Problems of one prose field (goal, why, scope text, ...)."""
    out = []
    if ACTION.search(text):
        out.append(f"{where}: ga act action line ('{ACTION.search(text).group(0).strip()}')")
    if MARKERS.search(text):
        out.append(f"{where}: edit/patch marker ('{MARKERS.search(text).group(0).strip()}')")
    if FENCE.search(text):
        out.append(f"{where}: fenced code")
    n = len(CODE_LINE.findall(text))
    if n > CODE_LINES_MAX:
        out.append(f"{where}: {n} code-like lines (max {CODE_LINES_MAX})")
    return out


def _strings(obj, path: str):
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from _strings(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _strings(v, f"{path}[{i}]")


def mail_problems(text: str) -> list[str]:
    """Problems of one mail body (```ga head + optional ```ga-act block); [] when it is WHAT only."""
    out = []
    blocks = BLOCK.findall(text)
    rest = BLOCK.sub("", text)
    if FENCE.search(rest):
        out.append("mail: fenced block outside the ga / ga-act blocks")
    out += [p for p in text_problems("mail body", rest) if "fenced" not in p]
    for kind, body in blocks:
        try:
            obj = json.loads(body)
        except json.JSONDecodeError as e:
            out.append(f"{kind}: not JSON ({e})")
            continue
        tests = obj.pop("tests", {}) if kind == "ga-act" and isinstance(obj, dict) else {}
        if kind == "ga-act" and isinstance(obj, dict):
            for k in ("rewrite", "actions"):
                if k in obj:
                    out.append(f"ga-act: '{k}' key (baseline sends no actions)")
            if not isinstance(tests, dict) or any(not (TEST_PATH.match(str(p)) or p in SPEC_DATA) for p in tests):
                out.append("ga-act: tests may only be acceptance test files tests/test_*.py (+ ga/forms/registry.json)")
            for p in SPEC_DATA & set(tests if isinstance(tests, dict) else ()):
                try:
                    json.loads(tests[p])
                except (TypeError, json.JSONDecodeError):
                    out.append(f"ga-act: {p} must be JSON")
            goal = (obj.get("item") or {}).get("goal", "")
            if len(goal) > GOAL_MAX:
                out.append(f"ga-act item.goal: {len(goal)} chars (a prose spec fits in {GOAL_MAX})")
        if kind == "ga" and isinstance(obj, dict) and len(obj.get("goal", "")) > GOAL_MAX:
            out.append(f"ga goal: {len(obj['goal'])} chars (max {GOAL_MAX})")
        for path, s in _strings(obj, kind):
            if path.startswith("ga-act.commands"):
                continue  # argv lists (pytest command), not prose
            out += text_problems(path, s)
    return out


def check_mail(text: str) -> None:
    probs = mail_problems(text)
    if probs:
        raise CodeFound("no_code_from_baseline: " + "; ".join(probs))


def check_spec(spec: dict) -> None:
    """flow.py spec/1: no code in any field."""
    probs = [p for path, s in _strings(spec, "spec") for p in text_problems(path, s)]
    if probs:
        raise CodeFound("no_code_from_baseline: " + "; ".join(probs))


def _self_test() -> None:
    head = {"schema": "directive/2", "id": "CMD-X1", "goal": "Add a pure function ga.vm.x.score(rows) -> int that "
            "counts rows whose state is met; rules in the docstring of tests/test_x1.py."}
    act = {"item": {"id": "CMD-X1", "goal": head["goal"], "files": ["ga/vm/x.py"], "done_when": "test"},
           "tests": {"tests/test_x1.py": "import unittest\nfrom ga.vm.x import score\nclass T(unittest.TestCase):\n"
                                         "    def test(self):\n        self.assertEqual(score([]), 0)\n"},
           "commands": {"commands": {"test": ["{python}", "-m", "pytest", "tests/test_x1.py"]}}, "base": "main"}

    def mail(h, a):
        return "```ga\n" + json.dumps(h) + "\n```\n\n```ga-act\n" + json.dumps(a) + "\n```\n"

    assert mail_problems(mail(head, act)) == [], mail_problems(mail(head, act))
    bad = [
        {**act, "item": {**act["item"], "goal": head["goal"] + "\nEDIT ga/vm/x.py\nSEARCH\nx = 1\nREPLACE\nx = 2"}},
        {**act, "item": {**act["item"], "goal": "write this:\ndef score(rows):\n    n = 0\n    return n\n"}},
        {**act, "item": {**act["item"], "goal": "```python\nprint(1)\n```"}},
        {**act, "tests": {**act["tests"], "ga/vm/x.py": "def score(rows): return 0\n"}},
        {**act, "rewrite": ["ga/vm/x.py"]},
        {**act, "item": {**act["item"], "goal": "x" * (GOAL_MAX + 1)}},
    ]
    for b in bad:
        assert mail_problems(mail(head, b)), b
    assert mail_problems(mail({**head, "goal": "NEW ga/vm/x.py\nimport os"}, act))
    check_spec({"id": "S1", "goal": "the VM reports its SHA", "acceptance": ["ga vm sha prints 40 hex"]})
    try:
        check_spec({"id": "S1", "goal": "def f():\n  a = 1\n  return a\n"})
    except CodeFound:
        pass
    else:
        raise AssertionError("code in spec/1 passed")
    # the group 4 mails (edit lists written by baseline) must be rejected
    g4 = Path(__file__).resolve().parent / "requests" / "G4" / "actions"
    for f in sorted(g4.glob("*.txt")):
        assert text_problems(f.name, f.read_text(encoding="utf-8")), f.name
    print("nocode self-test OK")


def main(argv: list[str]) -> int:
    if argv == ["--self-test"]:
        _self_test()
        return 0
    rc = 0
    for p in argv:
        probs = mail_problems(Path(p).read_text(encoding="utf-8"))
        for x in probs:
            print(f"{p}: {x}")
        rc |= bool(probs)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
