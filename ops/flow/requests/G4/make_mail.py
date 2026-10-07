"""Group 4 (research/VM_INTERIOR_DESIGN.md §12: VI-11, VI-12) as ga-act directives to the VM bridge, written under the
user's spec_split policy (10-07 12:3x) and the group 3 rev 2 method: baseline writes the spec, the acceptance test and
the exact ga act actions (actions/<id>.txt: NEW whole files, EDIT with verbatim SEARCH anchors from cec66f2); the
worker pastes them in turn 1. The acceptance test may not be edited.
    python3 make_mail.py <mailbox worktree> [ID ...]   -> writes to/AGY/<ts>-baseline-<id>.md
                                                          (default: CMD-VIR11 CMD-VIV11 CMD-VID12)

CMD-VIR11  VI-11a  rule/1 table O1 O2 O4 O7, action-spec/1 table, Guard (pure).        ga/vm/ops_rules.py
CMD-VIV11  VI-11b  VERIFY: postcondition in window_ms, one rung up, twice = BLOCKED.   ga/vm/ops_verify.py
CMD-VIT11  VI-11c  `ga ops tick` in shadow: observe -> rules -> Guard -> VERIFY -> alerts (ga.watch.tick).
                                                                                       ga/vm/ops.py, ga/__main__.py
CMD-VID12  VI-12   DORA metrics + optional slo.json checks from the journal (structure only, no console panel).
                                                                                       ga/vm/dora.py
Every item starts from vm/G4-INT (cec66f2 = 222ca6a + ISO-1). CMD-VIT11 builds on CMD-VIR11 and CMD-VIV11 (after):
send it only once both are integrated into vm/G4-INT.
VI-09 stays held (VI-08 held under spec_split). 0 model calls and no session on every path (tests).
Every directive head is checked with ga.forms (parse_text, validate, 0 hard problems) before it is written; every
action file is parsed with ga.act.fmt and may only touch its item's files.
"""
import json
import os
import re
import sys
from datetime import datetime, UTC
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODEL = "gemini-3.7-flash-medium"  # the worker model of every group 4 item (baseline may change it after a model bench)
BASE = "vm/G4-INT"  # ga-sdk cec66f2 = 222ca6a (group 3 deployed) + ISO-1; every group 4 item starts here
WHY = ("user 10-07 12:3x policy spec_split; group 4 of research/VM_INTERIOR_DESIGN.md §12 (VI-11, VI-12). Baseline "
       "wrote the spec, the acceptance test (may not be edited) and the exact actions; the worker applies them.")
ID_RE = re.compile(r"^CMD-[A-Z]+\d+$")


def pytest_cmd(*files):
    return ["{python}", "-m", "pytest", "-q", "-p", "no:cacheprovider", *files]


PASTE = ("Turn 1: answer with exactly the actions below, copied byte for byte (NEW blocks are whole new files; EDIT "
         "SEARCH blocks are verbatim lines of ga-sdk cec66f2, each matching once; they are complete: nothing else needs "
         "changing). Do not NEED or read any other file; do not RUN test before every action below is applied. If a "
         "block is rejected, resend only that block, fixed from the nearest lines the next card shows. Do not edit any "
         "test file. Do not explore.\n\n")


def actions(item_id):
    """The exact ga act actions of an item (actions/<id>.txt); make_mail checks them with ga.act.fmt.parse."""
    return (HERE / "actions" / f"{item_id}.txt").read_text(encoding="utf-8")


VIR11_GOAL = ("The Ops worker's rule/1 table (O1 cap_reached, O2 decide_no_model, O4 mut_survived, O7 base_drift), "
              "action-spec/1 table and Guard as pure code, 0 model calls; one new file ga/vm/ops_rules.py; rules: "
              "docstring of tests/test_vi11a_rules.py. " + PASTE + actions("CMD-VIR11"))
VIV11_GOAL = ("VERIFY for the Ops worker (postcondition inside window_ms, one rung up on failure, the same failure twice "
              "= BLOCKED, no endless retry), pure code; one new file ga/vm/ops_verify.py; rules: docstring of "
              "tests/test_vi11b_verify.py. " + PASTE + actions("CMD-VIV11"))
VIT11_GOAL = ("`ga ops tick` in shadow (observe shadow.jsonl -> rule/1 -> Guard -> VERIFY -> alerts through ga.watch.tick "
              "into an outbox file; nothing mailed, 0 model calls, no session): new ga/vm/ops.py and one line in "
              "ga/__main__.py OWN_PARSER; rules: docstring of tests/test_vi11c_tick.py. " + PASTE + actions("CMD-VIT11"))
VID12_GOAL = ("DORA metrics and SLO checks from the journal (journal/1) and the Ops rows, 0 model calls; slo.json is "
              "optional (the targets are the owner's: without it no target is checked); one new file ga/vm/dora.py; "
              "rules: docstring of tests/test_vi12_dora.py. " + PASTE + actions("CMD-VID12"))

ITEMS = [
    dict(id="CMD-VIR11", vi="VI-11a", test="test_vi11a_rules.py", files=["ga/vm/ops_rules.py"],
         guards=["tests/test_vi04b_shadow_verdict.py", "tests/test_vi05_watch.py"], goal=VIR11_GOAL,
         title="VI-11a Ops rule/1 table O1 O2 O4 O7 + action-spec/1 + Guard (pure, 0 model calls)"),
    dict(id="CMD-VIV11", vi="VI-11b", test="test_vi11b_verify.py", files=["ga/vm/ops_verify.py"],
         guards=["tests/test_vi05_watch.py", "tests/test_vi10a_journal.py"], goal=VIV11_GOAL,
         title="VI-11b Ops VERIFY: window_ms, one rung up, twice = BLOCKED (pure)"),
    dict(id="CMD-VIT11", vi="VI-11c", test="test_vi11c_tick.py", after=["CMD-VIR11", "CMD-VIV11"],
         files=["ga/vm/ops.py", "ga/__main__.py"],
         guards=["tests/test_vi11a_rules.py", "tests/test_vi11b_verify.py", "tests/test_vi05_watch.py",
                 "tests/test_cli.py"], goal=VIT11_GOAL,
         title="VI-11c `ga ops tick` in shadow: rules -> Guard -> VERIFY -> alerts (0 model calls, no session)"),
    dict(id="CMD-VID12", vi="VI-12", test="test_vi12_dora.py", files=["ga/vm/dora.py"],
         guards=["tests/test_vi10a_journal.py", "tests/test_vi10b_machine.py"], goal=VID12_GOAL,
         title="VI-12 DORA metrics + optional slo.json checks from the journal (structure only)"),
]
DEFAULT = ["CMD-VIR11", "CMD-VIV11", "CMD-VID12"]  # CMD-VIT11 once CMD-VIR11 and CMD-VIV11 are integrated


def directive(it):
    head = {"schema": "directive/2", "id": it["id"], "rev": 1, "to": "AGY", "after": it.get("after", []),
            "goal": f"{it['title']}: {it['goal'].split(PASTE)[0]}(the exact actions are in the ga-act item goal)"[:1800],
            "why": WHY,
            "scope": [{"id": "S1", "text": "only " + ", ".join(it["files"]) + " in a ga-sdk worktree; the tests are baseline's"}],
            "done_when": [{"id": "D1", "text": "ga act ends done: tests/" + it["test"] + " and the guard tests pass; "
                                               "the report carries the pushed agv commit"}],
            "budget": {"claude_p_runs": 0}, "model": MODEL}
    given = {f"tests/{it['test']}": (HERE / "tests" / it["test"]).read_text(encoding="utf-8")}
    spec = {"item": {"id": it["id"], "goal": it["goal"], "files": it["files"], "done_when": "test"},
            "tests": given,
            "commands": {"commands": {"test": pytest_cmd(f"tests/{it['test']}", *it["guards"])}, "timeout_s": 900},
            "base": it.get("base", BASE), "repo": "ga-sdk"}
    return head, "```ga\n" + json.dumps(head, ensure_ascii=False) + "\n```\n\n```ga-act\n" + json.dumps(spec, ensure_ascii=False) + "\n```\n"


def check(it, head, text):
    sys.path.insert(0, os.environ.get("GA_SDK", "/home/user/ga-sdk"))
    from ga.forms import hard, parse_text, validate
    from ga.act import card as C
    from ga.act.fmt import parse
    from ga.ctxpack import tokens
    ids = {x["id"] for x in ITEMS}
    assert ID_RE.match(it["id"]), it["id"]
    assert it["files"] and all(isinstance(f, str) and f for f in it["files"]), it["id"]
    assert all(a in ids and a != it["id"] for a in it.get("after", [])), it["id"]
    parsed, _ = parse_text(text)
    assert parsed == head, it["id"]
    pa = parse(actions(it["id"]))
    assert not pa.problems and pa.actions and not pa.noise, (it["id"], pa.problems, pa.noise)
    assert all(a.kind in ("EDIT", "NEW") and a.arg in it["files"] for a in pa.actions), it["id"]
    assert C.redact(it["goal"])[1] == 0, it["id"]  # the card would withhold part of the code
    pre = C.prefix(it["id"], it["goal"], ["test"], it["files"], [], {"test": []})
    assert tokens(pre) <= C.DEFAULT_CAP - 1500, (it["id"], tokens(pre))  # room for the turn part of the card
    probs = hard(validate(parsed))
    assert probs == [], (it["id"], [str(p) for p in probs])


if __name__ == "__main__":
    box = Path(sys.argv[1])
    want = sys.argv[2:] or DEFAULT
    for it in ITEMS:
        if it["id"] not in want:
            continue
        head, text = directive(it)
        check(it, head, text)
        ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
        p = box / "to" / "AGY" / f"{ts}-baseline-{it['id']}.md"
        p.write_text(text, encoding="utf-8")
        print(p.name)
