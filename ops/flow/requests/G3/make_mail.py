"""Group 3 (research/VM_INTERIOR_DESIGN.md §12: VI-04b, VI-10) as ga-act directives to the VM bridge, written under the
user's spec_split policy (10-07 12:3x): baseline writes the spec and the acceptance test, the worker implements; every
goal names the files, signatures, rules and code sites; the acceptance test may not be edited.
    python3 make_mail.py <mailbox worktree> [ID ...]   -> writes to/AGY/<ts>-baseline-<id>.md (default: CMD-VIB4 CMD-VIJ10)

CMD-VIB4   VI-04b  shadow hub decision = ga verdict (0 model calls).            ga/hub.py
CMD-VIJ10  VI-10a  journal/1 form (registry given) + fold(journal).             ga/forms/kinds.py, ga/vm/journal.py, docs/FORMS.md
CMD-VIM10  VI-10b  state machine T1-T11 in shadow, T2-T4 as would_do, replay.  ga/vm/machine.py
CMD-VIM10 builds on CMD-VIJ10 (after): send it only once CMD-VIJ10 is integrated into BASE.
Every directive head is checked with ga.forms (parse_text, validate, 0 hard problems) before it is written.
rev 2 (coordinator 10-07, both rev 1 orders unmet at turn cap 10 on gemini-3.7-flash-medium): each goal carries the
item's exact ga act actions from actions/<id>.txt (EDIT with verbatim SEARCH anchors from 0547772, NEW whole files,
RUN gendoc), so the worker pastes them in turn 1. make_mail parses them with ga.act.fmt before writing.
"""
import json
import os
import re
import sys
from datetime import datetime, UTC
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = "claude/gracious-meitner-vp49xe"  # ga-sdk integration head 0547772 (group 2 deployed)
WHY = ("user 10-07 12:3x policy spec_split; group 3 of research/VM_INTERIOR_DESIGN.md §12. Baseline wrote the spec "
       "and the acceptance test (may not be edited); the worker implements exactly what the goal names.")
ID_RE = re.compile(r"^CMD-[A-Z]+\d+$")
NO_EXPLORE = (" Do not explore: every file, line site, signature and rule you need is in this goal and in the test's "
              "docstring. Do not edit any test file.")


def pytest_cmd(*files):
    return ["{python}", "-m", "pytest", "-q", "-p", "no:cacheprovider", *files]


PASTE = ("Turn 1: answer with exactly the actions below, copied byte for byte (EDIT SEARCH blocks are verbatim lines of "
         "ga-sdk 0547772, each matching once; they are complete: nothing else needs changing). Do not NEED or read any "
         "other file; do not RUN test before every action below is applied. If a block is rejected, resend only that "
         "block, fixed from the nearest lines the next card shows. Do not edit any test file or given file.\n\n")


def actions(item_id):
    """The exact ga act actions of an item (actions/<id>.txt); make_mail checks them with ga.act.fmt.parse."""
    return (HERE / "actions" / f"{item_id}.txt").read_text(encoding="utf-8")


VIB4_GOAL = ("Shadow hub decision = ga verdict, 0 model calls; only ga/hub.py (MailHub.__init__ verdict_fn, MailHub._one "
             "shadow branch, new MailHub._verdict_decision, _SAME SHADOW). Rules: docstring of "
             "tests/test_vi04b_shadow_verdict.py. The amended guard tests (test_ga42_shadow, test_ga45, test_ga49, "
             "test_ga50, test_ga51) are given. " + PASTE + actions("CMD-VIB4"))
VIJ10_GOAL = ("journal/1 in the forms (ga/forms/registry.json is given; do not edit it) + ga/vm/journal.py (fold); "
              "rules: docstring of tests/test_vi10a_journal.py. The RUN gendoc at the end rewrites docs/FORMS.md from "
              "the registry (run it after the edits, in the same answer). " + PASTE + actions("CMD-VIJ10"))
VIM10_GOAL = ("The work-item state machine T1-T11 in shadow (no sessions; T2-T4 and T6' as would_do) + replay; one new "
              "file ga/vm/machine.py; rules: docstring of tests/test_vi10b_machine.py. " + PASTE + actions("CMD-VIM10"))

ITEMS = [
    dict(id="CMD-VIB4", rev=2, rev_note="rev 1 hit the turn cap at 2 of 4 edits; the goal now carries the exact EDIT actions",
         vi="VI-04b", model="gemini-3.7-flash-medium", test="test_vi04b_shadow_verdict.py",
         files=["ga/hub.py"],
         guards=["tests/test_ga42.py", "tests/test_ga42_shadow.py", "tests/test_ga45.py", "tests/test_ga49.py",
                 "tests/test_ga50.py", "tests/test_ga51.py", "tests/test_verdict.py", "tests/test_r1_gateway.py"],
         provided={f"tests/{n}": f"tests/given/{n}" for n in
                   ("test_ga42_shadow.py", "test_ga45.py", "test_ga49.py", "test_ga50.py", "test_ga51.py")},
         goal=VIB4_GOAL,
         title="VI-04b shadow hub decision = ga verdict (remove the model turn from the shadow path)"),
    dict(id="CMD-VIJ10", rev=2, rev_note="rev 1 hit the turn cap with no edit; the goal now carries the exact EDIT/NEW/RUN actions",
         vi="VI-10a", model="gemini-3.7-flash-medium", test="test_vi10a_journal.py",
         files=["ga/forms/kinds.py", "ga/vm/journal.py", "docs/FORMS.md"],
         guards=["tests/test_vi06_registry.py", "tests/test_forms.py", "tests/test_wire.py", "tests/test_mailbox.py"],
         provided={"ga/forms/registry.json": "registry.json"}, extra_commands={
             "gendoc": ["{python}", "-c", "from ga.forms import registry as R; "
                        "open('docs/FORMS.md', 'w', encoding='utf-8').write(R.render_doc(R.load()))"]},
         goal=VIJ10_GOAL,
         title="VI-10a journal/1 form in the registry + fold(journal)"),
    dict(base="vm/G3-INT", id="CMD-VIM10", vi="VI-10b", model="gemini-3.7-flash-medium", test="test_vi10b_machine.py", after=["CMD-VIJ10"],
         files=["ga/vm/machine.py"],
         guards=["tests/test_vi10a_journal.py", "tests/test_vi06_registry.py"],
         goal=VIM10_GOAL,
         title="VI-10b state machine T1-T11 in shadow (no sessions; T2-T4 as would_do) + replay"),
]
DEFAULT = ["CMD-VIB4", "CMD-VIJ10"]  # CMD-VIM10 once CMD-VIJ10 is integrated


def directive(it):
    rev = it.get("rev", 1)
    head = {"schema": "directive/2", "id": it["id"], "rev": rev, "to": "AGY", "after": it.get("after", []),
            "goal": f"{it['title']}: {it['goal'].split(PASTE)[0]}(the exact actions are in the ga-act item goal)"[:1800], "why": WHY,
            "scope": [{"id": "S1", "text": "only " + ", ".join(it["files"]) + " in a ga-sdk worktree; the tests are baseline's"}],
            "done_when": [{"id": "D1", "text": "ga act ends done: tests/" + it["test"] + " and the guard tests pass; "
                                               "the report carries the pushed agv commit"}],
            "budget": {"claude_p_runs": 0}, "model": it["model"]}
    if rev > 1:
        head["changes"] = [{"item": "D1", "op": "edit", "text": head["done_when"][0]["text"] + f" (rev {rev}: {it.get('rev_note', '')})"}]
    given = {f"tests/{it['test']}": (HERE / "tests" / it["test"]).read_text(encoding="utf-8")}
    given.update({dst: (HERE / src).read_text(encoding="utf-8") for dst, src in it.get("provided", {}).items()})
    spec = {"item": {"id": it["id"], "goal": it["goal"], "files": it["files"], "done_when": "test"},
            "tests": given,
            "commands": {"commands": {"test": pytest_cmd(f"tests/{it['test']}", *it["guards"]),
                                      **it.get("extra_commands", {})}, "timeout_s": 900},
            "base": it.get("base", BASE), "repo": "ga-sdk"}
    return head, "```ga\n" + json.dumps(head, ensure_ascii=False) + "\n```\n\n```ga-act\n" + json.dumps(spec, ensure_ascii=False) + "\n```\n"


def check(it, head, text):
    sys.path.insert(0, os.environ.get("GA_SDK", "/home/user/ga-sdk"))
    from ga.forms import hard, parse_text, validate
    assert ID_RE.match(it["id"]), it["id"]
    assert it["files"] and all(isinstance(f, str) and f for f in it["files"]), it["id"]
    parsed, _ = parse_text(text)
    assert parsed == head, it["id"]
    from ga.act.fmt import parse
    pa = parse(actions(it["id"]))
    assert not pa.problems and pa.actions, (it["id"], pa.problems)
    assert all(a.arg in it["files"] for a in pa.actions if a.kind in ("EDIT", "NEW")), it["id"]
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
