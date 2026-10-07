"""ACT-1 (user 10-07 17:3x "ga act 고치는 것부터 진행해"): ga act fixes as prose specs under policy
spec_split.no_code_from_baseline — goal = WHAT + rules + file/function names, plus baseline's acceptance test.
No edit lists, no code, no reference implementation. Every mail passes ops/flow/nocode.py before it is written.

    python3 make_mail.py <mailbox worktree> [ID ...]     (default: both; they are independent)

CMD-ACTR1  kept reads, outline for long files, per-turn trace in act/1      ga/act/loop.py, ga/act/retrieve.py, ga/act/card.py
CMD-ACTB1  per-directive max_turns (1-30, default 20), ## turns in report  ga/bridge/act.py
"""
import json
import re
import sys
from datetime import datetime, UTC
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import nocode  # noqa: E402

MODEL = "gemini-3.7-flash-medium"
BASE = "vm/G4-INT"  # ga-sdk c6f3f97 (ISO-1 + group 4)
WHY = ("user 10-07 17:1x-17:3x: baseline sends no code (policy spec_split.no_code_from_baseline); first fix ga act so "
       "a cheap model can work inside large files and failures are visible. The acceptance test may not be edited.")
ID_RE = re.compile(r"^CMD-[A-Z]+\d+$")
HOW = (" Read what you need with NEED (symbol / file lines a-b / grep), then edit. Edit only the listed files; do not "
       "edit any test. Keep every existing test green.")

ITEMS = [
    dict(id="CMD-ACTR1", test="test_act_reads.py", files=["ga/act/loop.py", "ga/act/retrieve.py", "ga/act/card.py"],
         guards=["tests/test_ga38.py", "tests/test_ga41.py", "tests/test_ga45.py", "tests/test_ga47.py",
                 "tests/test_act_isolation.py"],
         deselect=["tests/test_ga38.py::Loop::test_ts_fixture_seeded_bug_fixed"],
         title="ga act: kept reads, outline for long files, per-turn trace in act/1",
         goal=("ga act should let a cheap model work inside a large file. Three changes, rules R1-R3 in the docstring "
               "of tests/test_act_reads.py: R1 NEED results stay in the card on every later turn of the item (today "
               "Act keeps them for the next card only), re-served from the current files, dropped oldest first when "
               "the card is over its cap, at most 8. R2 NEED file on a file over 150 lines without 'lines a-b' "
               "answers with an outline (names of top-level defs/classes and methods with their line numbers) plus "
               "a hint to ask for lines. R3 Result.to_dict adds 'trace', one row per model turn (turn, card_tokens, "
               "actions as '<KIND> <arg>', applied, rejected, dropped). Where things are: class Act in "
               "ga/act/loop.py (units, _act, _run, Result), ga/act/retrieve.py (file_slice, symbol), "
               "ga/act/card.py (build, the drop order).") + HOW),
    dict(id="CMD-ACTB1", test="test_bridge_act_turns.py", files=["ga/bridge/act.py"],
         guards=["tests/test_vm_bridge_act.py"], deselect=[],
         title="ga bridge: per-directive max_turns and a ## turns section in the report",
         goal=("The bridge's code-work path should let each directive set the ga act turn cap and should mail back "
               "the per-turn trace. Rules B1-B3 in the docstring of tests/test_bridge_act_turns.py: B1 the ga-act "
               "block may carry max_turns, an int 1-30 (else item_spec raises ValueError), passed to ga act as "
               "--max-turns. B2 without it: the config's act.max_turns, else 20. B3 report() adds a '## turns' "
               "section after '## ga act result' with one line per trace row in the given form, cut to 4000 "
               "characters; no trace, no section; the report/2 head is unchanged. Where things are: "
               "ga/bridge/act.py (SPEC_KEYS, item_spec, act_argv, report).") + HOW),
]


def pytest_cmd(it):
    return ["{python}", "-m", "pytest", "-q", "-p", "no:cacheprovider", f"tests/{it['test']}", *it["guards"],
            *[x for d in it["deselect"] for x in ("--deselect", d)]]


def directive(it):
    head = {"schema": "directive/2", "id": it["id"], "rev": 1, "to": "AGY", "after": [],
            "goal": f"{it['title']}: {it['goal']}"[:1800], "why": WHY,
            "scope": [{"id": "S1", "text": "only " + ", ".join(it["files"]) + " in a ga-sdk worktree; the tests are baseline's"}],
            "done_when": [{"id": "D1", "text": "ga act ends done: tests/" + it["test"] + " and the guard tests pass; "
                                               "the report carries the pushed agv commit"}],
            "budget": {"claude_p_runs": 0}, "model": MODEL}
    spec = {"item": {"id": it["id"], "goal": it["goal"], "files": it["files"], "done_when": "test"},
            "tests": {f"tests/{it['test']}": (HERE / "tests" / it["test"]).read_text(encoding="utf-8")},
            "commands": {"commands": {"test": pytest_cmd(it)}, "timeout_s": 900}, "base": BASE, "repo": "ga-sdk"}
    return head, "```ga\n" + json.dumps(head, ensure_ascii=False) + "\n```\n\n```ga-act\n" + json.dumps(spec, ensure_ascii=False) + "\n```\n"


def check(it, head, text):
    sys.path.insert(0, "/home/user/ga-sdk")
    from ga.forms import hard, parse_text, validate
    assert ID_RE.match(it["id"]), it["id"]
    parsed, _ = parse_text(text)
    assert parsed == head, it["id"]
    assert hard(validate(parsed)) == [], it["id"]
    nocode.check_mail(text)


if __name__ == "__main__":
    box, want = Path(sys.argv[1]), sys.argv[2:] or [x["id"] for x in ITEMS]
    for it in ITEMS:
        if it["id"] in want:
            head, text = directive(it)
            check(it, head, text)
            ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
            (box / "to" / "AGY" / f"{ts}-baseline-{it['id']}.md").write_text(text, encoding="utf-8")
            print(f"{ts}-baseline-{it['id']}.md")
