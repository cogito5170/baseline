"""Baseline ops rules (research/GA_ENGINE_OPS.md O3, O5, O6, O8): observations in, actions out, no model.

The hourly routine (and the hub on events) gathers a small JSON and pipes it in; this file decides, the hub executes
the printed actions as written. Decisions are code; a model only runs what is printed.

    python3 ops/hub/ops_rules.py < obs.json          -> one JSON line per action (nothing printed = nothing to do)
    python3 ops/hub/ops_rules.py wire < mut.json     -> base64 of the JSON, relay-safe (O8)
    python3 ops/hub/ops_rules.py --self-test

obs.json:
    {"hub": {"id", "depth", "limit"},
     "sessions": [{"id", "title", "ctx", "bucket", "tags": [...]}],      # get_session of each ops/tokmon id (trimmed)
     "notifies": [{"from", "kind", "id", "tests"}]}                       # notify/1 lines received since the last run

Actions: {"action", "id", "why", ...}. State (what was already alerted) lives in ops/hub/ops_state.json.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RULES = {"ctx_limit": 150_000, "depth_margin": 1}
STATE = HERE / "ops_state.json"
SUCCESSOR = {"integrator": HERE / "successors"}  # <role key>.md, e.g. token_integrator.md, ga_sdk_integrator.md


def role(s: dict) -> str:
    tags = " ".join(s.get("tags") or [])
    t = (s.get("title") or "").lower()
    if "baseline-integrator" in tags or "통합" in t:
        return "integrator"
    if "baseline-worker" in tags or "cmd-" in t:
        return "worker"
    if "감시" in t or "watch" in t:
        return "watcher"
    return "other"


def successor_file(s: dict) -> Path | None:
    t = (s.get("title") or "").lower()
    key = "token_integrator" if "token" in t else "ga_sdk_integrator" if "ga-sdk" in t else None
    f = HERE / "successors" / f"{key}.md" if key else None
    return f if f and f.is_file() else None


FAILS = re.compile(r"(\d+)\s+fail")


def decide(obs: dict, state: dict) -> list[dict]:
    out: list[dict] = []
    alerted = state.setdefault("alerted", {})
    # O6: lineage depth — the hub itself
    h = obs.get("hub") or {}
    if isinstance(h.get("depth"), int) and isinstance(h.get("limit"), int):
        if h["depth"] >= h["limit"] - RULES["depth_margin"] and not alerted.get(f"depth:{h.get('id')}"):
            alerted[f"depth:{h.get('id')}"] = True
            out.append({"action": "alert_user", "id": h.get("id"), "why": f"lineage depth {h['depth']}/{h['limit']}: a hub "
                        "created from here cannot create workers", "do": "before the next handoff try a "
                        "create_new_session_on_fire routine for the new hub; if it lacks claude-code-remote tools, ask the "
                        "user once to open one hub session (prompt from STATE Handoff step 2)"})
    # O5: context over the limit
    for s in obs.get("sessions") or []:
        ctx = s.get("ctx")
        if not isinstance(ctx, int) or ctx <= RULES["ctx_limit"] or s.get("bucket") == "completed":
            continue
        r = role(s)
        if r == "integrator":
            f = successor_file(s)
            out.append({"action": "replace_integrator" if f else "request_successor_prompt", "id": s["id"],
                        "why": f"ctx {ctx} > {RULES['ctx_limit']}", "prompt_file": str(f.relative_to(HERE.parent.parent)) if f else None,
                        "do": ("create_session from prompt_file (update head/history line), archive old, swap the id in "
                               "STATE + ops/tokmon/sessions.txt, send 'hub is now' only if the hub changed")
                        if f else "ask it for a successor prompt, save to ops/hub/successors/<key>.md, then replace"})
        elif r == "worker":
            out.append({"action": "worker_checkpoint", "id": s["id"], "why": f"ctx {ctx} > {RULES['ctx_limit']}",
                        "do": "send: push what is green now and notify kind partial with what is left; then a fresh "
                              "worker on the same branch with the remaining scope"})
        elif r == "watcher":
            out.append({"action": "replace_watcher", "id": s["id"], "why": f"ctx {ctx}",
                        "do": "recreate the watcher from its first prompt; move its routine"})
    # O3: a worker reports failures — the claim "fails on base too" is checked in the integrator's env, never trusted
    for n in obs.get("notifies") or []:
        if n.get("kind") != "done":
            continue
        m = FAILS.search(str(n.get("tests") or ""))
        if m and int(m.group(1)) > 0:
            out.append({"action": "verdict_with_base_compare", "id": n.get("id"), "why": f"worker reports {m.group(1)} "
                        "failing (its env)", "do": "in the VERDICT ask the integrator to run the full suite on the branch "
                        "AND on the integration head in its env and report failing_vs_base; only new failures block"})
    return out


def wire(obj) -> str:
    """O8: the session relay HTML-escapes < > & and tool arguments decode \\u escapes, so mutations travel as base64
    of the UTF-8 JSON (one line, [A-Za-z0-9+/=] only). The receiver: `echo <b64> | base64 -d > mut.json`."""
    import base64
    return base64.b64encode(json.dumps(obj, ensure_ascii=False).encode("utf-8")).decode("ascii")


def _self_test() -> None:
    st: dict = {}
    obs = {"hub": {"id": "h", "depth": 7, "limit": 8},
           "sessions": [{"id": "a", "title": "baseline ◇ Token 통합", "ctx": 200_000, "tags": ["baseline-integrator"]},
                        {"id": "b", "title": "ga-sdk CMD-GA9", "ctx": 160_000, "tags": ["baseline-worker"]},
                        {"id": "c", "title": "x", "ctx": 10, "tags": []},
                        {"id": "d", "title": "ga-sdk CMD-GA8", "ctx": 900_000, "bucket": "completed", "tags": ["baseline-worker"]}],
           "notifies": [{"kind": "done", "id": "CMD-GA53", "tests": "1409 run, 10 failed"},
                        {"kind": "done", "id": "CMD-GA52", "tests": "1417 run, 0 failed"}]}
    acts = decide(obs, st)
    kinds = sorted(a["action"] for a in acts)
    assert kinds == ["alert_user", "replace_integrator", "verdict_with_base_compare", "worker_checkpoint"], kinds
    assert decide({"hub": obs["hub"]}, st) == [], "depth alert must fire once"
    w = wire([{"find": "a < b && c > d"}])
    import base64
    assert re.fullmatch(r"[A-Za-z0-9+/=]+", w) and json.loads(base64.b64decode(w)) == [{"find": "a < b && c > d"}]
    print("self-test ok")


def main(argv: list[str]) -> int:
    if argv[1:2] == ["--self-test"]:
        _self_test()
        return 0
    data = json.load(sys.stdin)
    if argv[1:2] == ["wire"]:
        print(wire(data))
        return 0
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    for a in decide(data, state):
        print(json.dumps(a, ensure_ascii=False))
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
