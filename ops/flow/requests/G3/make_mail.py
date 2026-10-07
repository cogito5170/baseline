"""Group 3 (research/VM_INTERIOR_DESIGN.md §12: VI-04b, VI-10) as ga-act directives to the VM bridge, written under the
user's spec_split policy (10-07 12:3x): baseline writes the spec and the acceptance test, the worker implements; every
goal names the files, signatures, rules and code sites; the acceptance test may not be edited.
    python3 make_mail.py <mailbox worktree> [ID ...]   -> writes to/AGY/<ts>-baseline-<id>.md (default: CMD-VIB4 CMD-VIJ10)

CMD-VIB4   VI-04b  shadow hub decision = ga verdict (0 model calls).            ga/hub.py
CMD-VIJ10  VI-10a  journal/1 form (registry given) + fold(journal).             ga/forms/kinds.py, ga/vm/journal.py, docs/FORMS.md
CMD-VIM10  VI-10b  state machine T1-T11 in shadow, T2-T4 as would_do, replay.  ga/vm/machine.py
CMD-VIM10 builds on CMD-VIJ10 (after): send it only once CMD-VIJ10 is integrated into BASE.
Every directive head is checked with ga.forms (parse_text, validate, 0 hard problems) before it is written.
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


VIB4_GOAL = (
    "Edit only ga/hub.py, class MailHub (the shadow hub; the non-shadow path and MailHub._decide stay as they are). "
    "(1) MailHub.__init__: add the keyword `verdict_fn: Callable[..., Any] | None = None` after `shadow`; in the body "
    "add `from . import verdict as V` next to `from . import judge as J`, and after `self.apply_fn = apply_fn or "
    "J.apply` add `self.verdict_fn = verdict_fn or V.dry_run`. "
    "(2) MailHub._one: directly after the line `outside = [f for f in changed if owned and not any(fnmatch(f, g) for "
    "g in owned)]` and before `card = verdict_card(...)` insert: "
    "`if self.shadow:` -> `decision, lines, err = self._verdict_decision(rp, rc, did, j.sha or commit.get(\"sha\", \"\"), "
    "owned, list(getattr(j, \"needs\", None) or []))`; `self._usage, self._error, self._served = None, err, None`; "
    "`self._shadow(m, did, head, directive, j, decision, lines)`; `res.plan.append(f\"shadow {decision} {did}\")`; "
    "`return`. (The old `if self.shadow:` block further down then is only reached by the non-shadow path; leave it.) "
    "(3) NEW method MailHub._verdict_decision(self, rp: Path, rc: dict[str, Any], did: str, sha: str, owned: list[str], "
    "needs: list[str]) -> tuple[str, list[str], str], placed before _decide: `from . import verdict as V`; "
    "spec = (self.conf.get(\"specs\") or {}).get(did); if not spec and sha: base = V._rev(rp, rc[\"base\"]); added = "
    "[p for st, p in V._changed(rp, base, sha) if st == \"A\" and V._is_test(p) and Path(p).name.startswith(\"test_\")] "
    "if base else []; spec = added[0] if added else None. If not spec: return \"SHADOW\", [f\"no acceptance test for "
    "{did}\"], \"\". Then try: v = self.verdict_fn(rp, branch=sha, sha=sha, base=rc[\"base\"], spec=spec, "
    "allowed=owned or None, nonexec=needs or None, scope=str(self.conf.get(\"verdict_scope\", \"full\")), "
    "config=rc.get(\"config\")); except Exception as e: return \"SHADOW\", [f\"ga verdict failed: "
    "{type(e).__name__}\"], f\"verdict:{type(e).__name__}\". Return str(v[\"decision\"]), [str(v[\"reason\"])[:300]], "
    "\"\". No import of ga.llm, ga.backends or ga.act anywhere on this path. "
    "(4) The module dict `_SAME` (used by shadow_compare): add the entry \"SHADOW\": \"ASK_HUMAN\". "
    "The given guard tests tests/test_ga42_shadow.py, test_ga45.py, test_ga49.py, test_ga50.py, test_ga51.py are "
    "baseline's amendments for this change (shadow no longer makes a model turn); they are written into the worktree "
    "for you." + NO_EXPLORE)

VIJ10_GOAL = (
    "ga/forms/registry.json is given (baseline added enums JOURNAL_STATES, JOURNAL_EVENTS and form journal/1; do not "
    "edit it). (1) EDIT ga/forms/kinds.py: directly above the line `SCHEMAS: dict[str, tuple[...]] = {` add "
    "JOURNAL_STATES = tuple(_REG['enums']['JOURNAL_STATES']); JOURNAL_EVENTS = tuple(_REG['enums']['JOURNAL_EVENTS']); "
    "JOURNAL_TRANSITIONS (the exact dict in the test docstring, T11 -> (None, \"CANCELLED\")); "
    "JOURNAL_ITEM_RE = re.compile(r\"^(?:CMD-[A-Z]+\\d+|[A-Z][A-Z0-9]*-[A-Z]+-\\d+)$\"); a check _journal_guard(v) "
    "returning None when v is a dict with keys exactly {ok, why}, ok a bool and why a non-empty str, else an error "
    "string; JOURNAL = [Field(\"id\", matches(re.compile(r\"^J-[1-9]\\d*$\"), \"J-<n>\")), Field(\"at\", "
    "matches(re.compile(r\"^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$\"), \"YYYY-MM-DDTHH:MM:SSZ\")), Field(\"item\", "
    "matches(JOURNAL_ITEM_RE, \"a work/1 item id\")), Field(\"from_state\", one_of(\"NONE\", *JOURNAL_STATES)), "
    "Field(\"to_state\", one_of(\"NONE\", *JOURNAL_STATES)), Field(\"event\", one_of(*JOURNAL_EVENTS)), Field(\"guard\", "
    "_journal_guard), Field(\"inputs_hash\", matches(re.compile(r\"^[0-9a-f]{64}$\"), \"a sha256 hex digest\")), "
    "Field(\"record\", lambda v: None if isinstance(v, dict) else \"must be an object\")]; and "
    "_journal_cross(doc) -> list[Problem]: ev, f, t = doc event/from_state/to_state; if not doc[\"guard\"][\"ok\"]: "
    "return [] if f == t else [Problem(\"$.to_state\", \"a refused transition keeps the state\")]; want_f, want_t = "
    "JOURNAL_TRANSITIONS[ev]; ok when t == want_t and (f == want_f if want_f is not None else f not in (\"NONE\", "
    "\"CANCELLED\")), else [Problem(\"$.event\", f\"{ev} is {want_f or 'any state'} -> {want_t}, not {f} -> {t}\")]. "
    "Add \"journal/1\": (JOURNAL, _journal_cross) to SCHEMAS after \"notify/1\". "
    "(2) NEW ga/vm/journal.py with JournalError(ValueError), inputs_hash, fold, dumps, append, read exactly as the "
    "test docstring says (imports only hashlib, json, pathlib.Path, typing.Any and `from ..forms import hard, "
    "validate`; validate(row, \"journal/1\")). Write it with one NEW action. "
    "(3) RUN gendoc after your edits (writes docs/FORMS.md from the registry), then the test command, then DONE."
    + NO_EXPLORE)

VIM10_GOAL = (
    "NEW ga/vm/machine.py (one NEW action; no other file changes): the work-item state machine T1-T11 in shadow, "
    "exactly as the docstring of tests/test_vi10b_machine.py lists it (constants ACTIVE, DONE, WOULD_DO with the "
    "exact strings; class Machine with __init__(rows=()), step(ev) and a guard per event; replay(events)). Imports: "
    "`from __future__ import annotations`, re, `from typing import Any`, `from ..forms import hard, validate`, "
    "`from ..forms.kinds import JOURNAL_TRANSITIONS`, `from ..net.pool import _cycle, overlap`, `from .journal import "
    "JournalError, fold, inputs_hash`. Rules in order inside step: event not in JOURNAL_TRANSITIONS -> raise "
    "JournalError; cur = self.state.get(item, \"NONE\"); cur == \"NONE\" and event != \"T1\" -> raise JournalError; "
    "(ok, why, record) = self._guard(event, item, cur, inputs) where inputs = dict(ev.get(\"inputs\") or {}); "
    "to = JOURNAL_TRANSITIONS[event][1] if ok else cur; build the row dict (schema journal/1, id f\"J-{len(self.rows) + "
    "1}\", at = ev[\"at\"], inputs_hash(inputs)); hard(validate(row, \"journal/1\")) non-empty -> raise JournalError; "
    "append; if to != \"NONE\": self.state[item] = to; if event == \"T1\" and ok: self.items[item] = record[\"work\"]; "
    "return row. _guard: T11 first (CANCELLED -> refused, else ok with {\"reason\": ...}); then cur != "
    "JOURNAL_TRANSITIONS[event][0] -> (False, f\"{item} is {cur}, {event} needs {want}\", {}); then the per-event "
    "rules of the docstring; every refusal returns (False, <non-empty why>, {}). T6 counts earlier rows of the same "
    "item with event T6 and guard ok. T2/T6' use self.items[item] for after/files and self.items.get(o, {}).get("
    "\"files\", []) for the other active items." + NO_EXPLORE)

ITEMS = [
    dict(id="CMD-VIB4", vi="VI-04b", model="gemini-3.7-flash-medium", test="test_vi04b_shadow_verdict.py",
         files=["ga/hub.py"],
         guards=["tests/test_ga42.py", "tests/test_ga42_shadow.py", "tests/test_ga45.py", "tests/test_ga49.py",
                 "tests/test_ga50.py", "tests/test_ga51.py", "tests/test_verdict.py", "tests/test_r1_gateway.py"],
         provided={f"tests/{n}": f"tests/given/{n}" for n in
                   ("test_ga42_shadow.py", "test_ga45.py", "test_ga49.py", "test_ga50.py", "test_ga51.py")},
         goal=VIB4_GOAL,
         title="VI-04b shadow hub decision = ga verdict (remove the model turn from the shadow path)"),
    dict(id="CMD-VIJ10", vi="VI-10a", model="gemini-3.7-flash-medium", test="test_vi10a_journal.py",
         files=["ga/forms/kinds.py", "ga/vm/journal.py", "docs/FORMS.md"],
         guards=["tests/test_vi06_registry.py", "tests/test_forms.py", "tests/test_wire.py", "tests/test_mailbox.py"],
         provided={"ga/forms/registry.json": "registry.json"}, extra_commands={
             "gendoc": ["{python}", "-c", "from ga.forms import registry as R; "
                        "open('docs/FORMS.md', 'w', encoding='utf-8').write(R.render_doc(R.load()))"]},
         goal=VIJ10_GOAL,
         title="VI-10a journal/1 form in the registry + fold(journal)"),
    dict(id="CMD-VIM10", vi="VI-10b", model="gemini-3.7-flash-medium", test="test_vi10b_machine.py", after=["CMD-VIJ10"],
         files=["ga/vm/machine.py"],
         guards=["tests/test_vi10a_journal.py", "tests/test_vi06_registry.py"],
         goal=VIM10_GOAL,
         title="VI-10b state machine T1-T11 in shadow (no sessions; T2-T4 as would_do) + replay"),
]
DEFAULT = ["CMD-VIB4", "CMD-VIJ10"]  # CMD-VIM10 once CMD-VIJ10 is integrated


def directive(it):
    rev = it.get("rev", 1)
    head = {"schema": "directive/2", "id": it["id"], "rev": rev, "to": "AGY", "after": it.get("after", []),
            "goal": f"{it['title']}: {it['goal']}"[:1800], "why": WHY,
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
            "base": BASE, "repo": "ga-sdk"}
    return head, "```ga\n" + json.dumps(head, ensure_ascii=False) + "\n```\n\n```ga-act\n" + json.dumps(spec, ensure_ascii=False) + "\n```\n"


def check(it, head, text):
    sys.path.insert(0, os.environ.get("GA_SDK", "/home/user/ga-sdk"))
    from ga.forms import hard, parse_text, validate
    assert ID_RE.match(it["id"]), it["id"]
    assert it["files"] and all(isinstance(f, str) and f for f in it["files"]), it["id"]
    parsed, _ = parse_text(text)
    assert parsed == head, it["id"]
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
