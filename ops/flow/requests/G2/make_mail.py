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
    dict(id="CMD-VI3", rev=2, vi="VI-03", model="gemini-3.7-flash-medium", test="test_vi03_sites.py",
         files=["ga/llm/sites.json"], guards=["tests/test_r1_scan.py"],
         goal=("Write ga/llm/sites.json: a JSON list with one row per gated model turn under ga/ (each L.run_turn / "
               "llm.run_turn call outside ga/llm), keyed '<path under ga/>::<enclosing function qualname>' exactly as "
               "tests/test_vi03_sites.py computes it. Row = {site, purpose, ladder_step (cheap|strong|either), "
               "why_no_rule (>= 20 chars: why a fixed rule cannot decide this turn)}. purpose = the literal purpose= "
               "of that call when it has one. Read each call site to write an honest why_no_rule. "
               "rev 2 (rev 1 hit the turn cap with no edit): the 8 sites today are — "
               "act/loop.py::Act._call.turn (purpose build: the executor's edit turn on a work item), "
               "act/route.py::triage (diagnosis: one triage turn that picks a start model and turn cap), "
               "ask/model.py::one_turn (opinion: `ga ask` answers a person's free-text question), "
               "gemini.py::Supervisor._one_turn (probe: a supervise plan turn), "
               "hub.py::MailHub._decide (coordination: the shadow hub decides a mail's next step), "
               "intake/engine.py::Intake.send (intake: turns a person's request into a task form), "
               "net/node.py::Node._turn (build: a peer node's build turn), "
               "plan/draft.py::turn (plan: drafts a directive from a request). "
               "Write the whole file with one NEW action; no other file changes."),
         title="VI-03 per-site 'why no rule' table (the rewiring and the no-call-outside-gateway scan landed in R1)"),
    dict(id="CMD-VI7", vi="VI-07", model="gemini-3.7-flash-medium", test="test_vi07_status.py",
         files=["ga/llm/report.py"], guards=["tests/test_r1_gateway.py"],
         goal=("In ga/llm/report.py add status(report) -> status/1 dict {schema:'status/1', id:'LLM-<YYYYMMDDHH of "
               "report at>', items:[{id: cap, state: ok|near|over, note}], blockers:[{kind:'budget', what}]} — one item "
               "per cap that has a numeric limit and a spend (near = spend >= 80 % of limit, over = spend > limit); a "
               "blocker per over cap and one when policy_ok is false. Add --status to `ga llm report` to print it. "
               "Keep build() and the plain report unchanged. In main(): add p.add_argument('--status', "
               "action='store_true') and print status(rep) instead of rep when it is set."),
         title="VI-07 hourly gateway summary as status/1"),
    dict(id="CMD-VI5", rev=2, rev_note="goal spells out every rule and the notify/1 head", vi="VI-05", model="claude-sonnet-5-5-medium", test="test_vi05_watch.py",
         files=["ga/watch.py"], guards=[],
         goal=("Create ga/watch.py (DEV-WATCH): DEFAULTS {ctx_cap 150000, session_usd_per_h 5.0, total_usd_per_h 12.0, "
               "snapshot_max_age_s 7200, vm_usd_per_h 6.0}; load_thresholds(path) (Ops-owned JSON merged over "
               "DEFAULTS, missing file = DEFAULTS); rules(snapshot, prev, ledger_rows, thresholds, now) -> sorted "
               "alerts {kind, key, note} with kinds ctx_over, session_cost_rate, total_cost_rate, snapshot_stale "
               "(off when snapshot_max_age_s is None), vm_spend_rate (ledger usd in the last hour); tick(alerts, "
               "state_path, now, send) mails each (kind, key) once per UTC day as a valid notify/1 kind alert "
               "(ref = an https URL, note <= 280 chars) to baseline-ops, snapshot_stale also to baseline. No import "
               "of model code (llm, backends, adapters, gemini). All rules are in the test's docstring. Build the notify/1 "
               "text with ga.forms.dump_text(head). Write the whole file with one NEW action. "
               "rev 2 (rev 1 hit the turn cap with no edit; do not explore, everything needed is here): "
               "imports only json, datetime (datetime, timedelta, timezone), pathlib.Path and "
               "`from ga.forms import dump_text`. Times: parse 'YYYY-MM-DDTHH:MM:SSZ' with "
               "datetime.strptime(..., '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc). "
               "rules: live = sessions with status != 'archived' and bucket != 'completed'; ctx_over key=session id "
               "when ctx > ctx_cap (strictly). Cost rates need prev and snapshot: hours = (snap.at - prev.at) seconds/3600 "
               "(skip when <= 0); per session id present in both: (cost_now - cost_prev)/hours > session_usd_per_h -> "
               "session_cost_rate key=id; summed over all sessions in each snapshot: (sum_now - sum_prev)/hours > "
               "total_usd_per_h -> total_cost_rate key='total'. snapshot_stale key='snapshot' when snapshot_max_age_s is "
               "not None and (snapshot is None or now - snapshot.at > snapshot_max_age_s seconds); when snapshot is None "
               "no other snapshot rule runs. vm_spend_rate key='vm' when sum of row['usd'] for ledger rows with "
               "now - 1h < at <= now is > vm_usd_per_h. Each alert = {'kind','key','note'} (note: short text with the "
               "numbers); return sorted(alerts, key=lambda a: (a['kind'], a['key'])). "
               "tick: state file JSON {'sent': {'<kind>|<key>': 'YYYY-MM-DD'}} (missing = empty); day = now UTC date "
               "isoformat; for each alert not already sent today: for to in ['baseline-ops'] + (['baseline'] if kind == "
               "'snapshot_stale' else []): send(to, dump_text({'schema': 'notify/1', 'to': to, 'kind': 'alert', "
               "'ref': 'https://github.com/cogito5170/baseline/blob/claude/gracious-meitner-vp49xe/ops/hub/watch_thresholds.json', "
               "'id': f'WATCH-{kind}-{key}', 'note': note[:280]})); record it, append the alert to the returned list; "
               "write the state file (mkdir parents) at the end. DEFAULTS is a plain dict; load_thresholds returns "
               "{**DEFAULTS, **json.loads(file)} or dict(DEFAULTS) when the file does not exist."),
         title="VI-05 watcher core (rules, thresholds, once-a-day alerts; 0 model calls)"),
    dict(id="CMD-VI6", vi="VI-06", model="claude-sonnet-5-5-medium", test="test_vi06_registry.py",
         files=["ga/forms/registry.py", "ga/forms/kinds.py", "docs/FORMS.md"],
         guards=["tests/test_forms.py", "tests/test_wire.py", "tests/test_mailbox.py"],
         goal=("ga/forms/registry.json is given (baseline wrote it from today's kinds.py; do not edit it). "
               "(1) NEW ga/forms/registry.py: FILE = Path(__file__).with_name('registry.json'); load() -> the parsed "
               "JSON; render_doc(reg) -> a markdown string that names every form and every enum value (any stable "
               "layout). (2) EDIT ga/forms/kinds.py: replace the 8 hand-written tuples VERDICT_CLASSES, CAUSES, "
               "NEXT_CHOICES, HANDLED_STATUS, CHANGE_SIZES, NEEDS (lines 33-38), BLOCKER_KINDS (124) and NOTIFY_KINDS "
               "(126) with NAME = tuple(_REG['enums']['NAME']), where _REG = load() is imported from .registry above "
               "line 33 (from .registry import load as _load_registry; _REG = _load_registry()). (3) RUN gendoc (after your edits) to "
               "write docs/FORMS.md from the registry, then DONE. Values stay the same, so nothing valid becomes invalid."),
         provided={"ga/forms/registry.json": "registry.json"}, extra_commands={
             "gendoc": ["{python}", "-c", "from ga.forms import registry as R; "
                        "open('docs/FORMS.md', 'w', encoding='utf-8').write(R.render_doc(R.load()))"]},
         title="VI-06 forms registry, ga-sdk side (baseline flow.py vendored copy is a separate item)"),
]


def directive(it):
    rev = it.get("rev", 1)
    head = {"schema": "directive/2", "id": it["id"], "rev": rev, "to": "AGY", "after": [],
            "goal": f"{it['title']}: {it['goal']}"[:1800], "why": WHY,
            "scope": [{"id": "S1", "text": "only " + ", ".join(it["files"]) + " in a ga-sdk worktree; the tests are baseline's"}],
            "done_when": [{"id": "D1", "text": "ga act ends done: tests/" + it["test"] + " and the guard tests pass; "
                                               "the report carries the pushed agv commit"}],
            "budget": {"claude_p_runs": 0}, "model": it["model"]}
    if rev > 1:
        head["changes"] = [{"item": "D1", "op": "edit", "text": head["done_when"][0]["text"] + f" (rev {rev}: {it.get('rev_note', 'goal names the sites')})"}]
    given = {f"tests/{it['test']}": (HERE / "tests" / it["test"]).read_text(encoding="utf-8")}
    given.update({dst: (HERE / src).read_text(encoding="utf-8") for dst, src in it.get("provided", {}).items()})
    spec = {"item": {"id": it["id"], "goal": it["goal"], "files": it["files"], "done_when": "test"},
            "tests": given,
            "commands": {"commands": {"test": pytest_cmd(f"tests/{it['test']}", *it["guards"]),
                                      **it.get("extra_commands", {})}, "timeout_s": 900},
            "base": BASE, "repo": "ga-sdk"}
    return "```ga\n" + json.dumps(head, ensure_ascii=False) + "\n```\n\n```ga-act\n" + json.dumps(spec, ensure_ascii=False) + "\n```\n"


if __name__ == "__main__":
    box = Path(sys.argv[1])
    for it in ITEMS:
        ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
        p = box / "to" / "AGY" / f"{ts}-baseline-{it['id']}.md"
        p.write_text(directive(it), encoding="utf-8")
        print(p.name)
