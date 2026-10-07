"""Group 2 (research/VM_INTERIOR_DESIGN.md §12) as ga-act directives to the VM bridge: one item per VI id, the acceptance
test written by baseline (tests/<file>), run with pytest in the ga-sdk worktree together with guard tests.
    python3 make_mail.py <mailbox worktree>   -> writes to/AGY/<ts>-baseline-<id>.md
"""
import json
import sys
from datetime import datetime, UTC
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = "claude/gracious-meitner-vp49xe"  # ga-sdk integration head 19dc227 (group 1 deployed)
WHY = ("User 10-07 11:3x: send group 2 of the VM interior build order (research/VM_INTERIOR_DESIGN.md §12) to the VM; "
       "the acceptance test is baseline's and may not be edited.")


def pytest_cmd(*files):
    return ["{python}", "-m", "pytest", "-q", "-p", "no:cacheprovider", *files]


ITEMS = [
    dict(id="CMD-VI3", vi="VI-03", model="gemini-3.7-flash-medium", test="test_vi03_sites.py",
         files=["ga/llm/sites.json"], guards=["tests/test_r1_scan.py"],
         goal=("Write ga/llm/sites.json: a JSON list with one row per gated model turn under ga/ (each L.run_turn / "
               "llm.run_turn call outside ga/llm), keyed '<path under ga/>::<enclosing function qualname>' exactly as "
               "tests/test_vi03_sites.py computes it. Row = {site, purpose, ladder_step (cheap|strong|either), "
               "why_no_rule (>= 20 chars: why a fixed rule cannot decide this turn)}. purpose = the literal purpose= "
               "of that call when it has one. Read each call site to write an honest why_no_rule."),
         title="VI-03 per-site 'why no rule' table (the rewiring and the no-call-outside-gateway scan landed in R1)"),
    dict(id="CMD-VI7", vi="VI-07", model="gemini-3.7-flash-medium", test="test_vi07_status.py",
         files=["ga/llm/report.py"], guards=["tests/test_r1_gateway.py"],
         goal=("In ga/llm/report.py add status(report) -> status/1 dict {schema:'status/1', id:'LLM-<YYYYMMDDHH of "
               "report at>', items:[{id: cap, state: ok|near|over, note}], blockers:[{kind:'budget', what}]} — one item "
               "per cap that has a numeric limit and a spend (near = spend >= 80 % of limit, over = spend > limit); a "
               "blocker per over cap and one when policy_ok is false. Add --status to `ga llm report` to print it. "
               "Keep build() and the plain report unchanged."),
         title="VI-07 hourly gateway summary as status/1"),
    dict(id="CMD-VI5", vi="VI-05", model="claude-sonnet-5-5-medium", test="test_vi05_watch.py",
         files=["ga/watch.py"], guards=[],
         goal=("Create ga/watch.py (DEV-WATCH): DEFAULTS {ctx_cap 150000, session_usd_per_h 5.0, total_usd_per_h 12.0, "
               "snapshot_max_age_s 7200, vm_usd_per_h 6.0}; load_thresholds(path) (Ops-owned JSON merged over "
               "DEFAULTS, missing file = DEFAULTS); rules(snapshot, prev, ledger_rows, thresholds, now) -> sorted "
               "alerts {kind, key, note} with kinds ctx_over, session_cost_rate, total_cost_rate, snapshot_stale "
               "(off when snapshot_max_age_s is None), vm_spend_rate (ledger usd in the last hour); tick(alerts, "
               "state_path, now, send) mails each (kind, key) once per UTC day as a valid notify/1 kind alert "
               "(ref = an https URL, note <= 280 chars) to baseline-ops, snapshot_stale also to baseline. No import "
               "of model code (llm, backends, adapters, gemini). All rules are in the test's docstring."),
         title="VI-05 watcher core (rules, thresholds, once-a-day alerts; 0 model calls)"),
    dict(id="CMD-VI6", vi="VI-06", model="claude-sonnet-5-5-medium", test="test_vi06_registry.py",
         files=["ga/forms/registry.json", "ga/forms/registry.py", "ga/forms/kinds.py", "docs/FORMS.md"],
         guards=["tests/test_forms.py", "tests/test_wire.py", "tests/test_mailbox.py"],
         goal=("Make ga/forms/registry.json (schema forms-registry/1: enums {NOTIFY_KINDS, HANDLED_STATUS, "
               "BLOCKER_KINDS, CHANGE_SIZES, NEEDS, VERDICT_CLASSES, CAUSES, NEXT_CHOICES: values}, forms {every form "
               "in ga.forms.kinds.SCHEMAS: {fields: {name: {required}}}}) the single source: ga/forms/registry.py with "
               "load() and render_doc(reg) -> markdown; kinds.py reads those enums from the registry (no hand-written "
               "tuples left); docs/FORMS.md = render_doc(load()). Same values as today: nothing valid becomes invalid."),
         title="VI-06 forms registry, ga-sdk side (baseline flow.py vendored copy is a separate item)"),
]


def directive(it):
    head = {"schema": "directive/2", "id": it["id"], "rev": 1, "to": "AGY", "after": [],
            "goal": f"{it['title']}: {it['goal']}"[:1800], "why": WHY,
            "scope": [{"id": "S1", "text": "only " + ", ".join(it["files"]) + " in a ga-sdk worktree; the tests are baseline's"}],
            "done_when": [{"id": "D1", "text": "ga act ends done: tests/" + it["test"] + " and the guard tests pass; "
                                               "the report carries the pushed agv commit"}],
            "budget": {"claude_p_runs": 0}, "model": it["model"]}
    spec = {"item": {"id": it["id"], "goal": it["goal"], "files": it["files"], "done_when": "test"},
            "tests": {f"tests/{it['test']}": (HERE / "tests" / it["test"]).read_text(encoding="utf-8")},
            "commands": {"commands": {"test": pytest_cmd(f"tests/{it['test']}", *it["guards"])}, "timeout_s": 900},
            "base": BASE, "repo": "ga-sdk"}
    return "```ga\n" + json.dumps(head, ensure_ascii=False) + "\n```\n\n```ga-act\n" + json.dumps(spec, ensure_ascii=False) + "\n```\n"


if __name__ == "__main__":
    box = Path(sys.argv[1])
    for it in ITEMS:
        ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
        p = box / "to" / "AGY" / f"{ts}-baseline-{it['id']}.md"
        p.write_text(directive(it), encoding="utf-8")
        print(p.name)
