"""baseline flow (user 10-06 21:2x): roles and who-may-send-what-to-whom are CODE, not prompt text.

Roles: baseline (DevOps top: spec-only requests to Dev/Ops, asks their opinions, synthesizes for the user),
Dev (plans + builds; reports releases to Ops), Ops (batches parallel specs for Dev, schedules, verifies, operates).
Every message is a JSON file under ops/flow/inbox/<to>/ committed to the baseline integration branch; this script is
the ONLY writer. It rejects a form a role may not send, a spec that carries method/plan fields, and out-of-scope work.

    python3 ops/flow/flow.py send <from> <to> <form> <file.json>   -> validates, writes inbox/<to>/<ts>-<from>-<form>-<id>.json
    python3 ops/flow/flow.py inbox <role> [--since <ts>]            -> new messages for a role (one JSON per line)
    python3 ops/flow/flow.py --self-test

Forms (all carry id, from, to, at):
  spec/1    {id, goal, why, acceptance:[...], constraints:[...], stage}      baseline->dev|ops ; ops->dev (inside batch)
  batch/1   {id, specs:[spec/1...], parallel:[[ids]...], order:[ids], why}   ops->dev   (parallel groups decided by Ops)
  release/1 {id, specs:[ids], repo, branch, sha, tests, mutations}           dev->ops   (built; Ops verifies/deploys)
  verify/1  {id, release, result: ok|incident, evidence, slo}                ops->dev
  incident/1{id, kind, evidence, cause, impact}                              ops->dev | ops->baseline
  opinion/1 {id, question, agree, disagree, missing, facts, risk, first_step} dev|ops->baseline ; any session->dev|ops
  ask/1     {id, question, context}                                          baseline->dev|ops ; dev|ops->their sessions
  status/1  {id, items:[{id,state,note}], blockers}                          dev|ops->baseline
  shadow/1  {id, actor, action, rejected_by, reason, would_do, evidence}     dev|ops->baseline. Scope (user 10-06 21:4x,
            option 1): ONLY a ga-engine internal rejection (rejected_by in SHADOW_SOURCES: guard, sensor, runtime, budget,
            policy) — the action is not executed, its would-be effect is recorded, independent work continues, and the
            user gets only these rows (batched). A Claude Code / platform permission denial is NOT a shadow case: the
            session stops that action and reports it to the user directly.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
KST = timezone(timedelta(hours=9))
ROLES = ("baseline", "dev", "ops", "session")
EDGES = {  # (from, to): forms allowed
    ("baseline", "dev"): {"spec/1", "ask/1"}, ("baseline", "ops"): {"spec/1", "ask/1"},
    ("ops", "dev"): {"batch/1", "verify/1", "incident/1"}, ("dev", "ops"): {"release/1", "opinion/1", "status/1"},
    ("dev", "baseline"): {"opinion/1", "status/1", "shadow/1"}, ("ops", "baseline"): {"opinion/1", "status/1", "incident/1", "shadow/1"},
    ("dev", "session"): {"ask/1"}, ("ops", "session"): {"ask/1"},
    ("session", "dev"): {"opinion/1"}, ("session", "ops"): {"opinion/1"},
}
REQUIRED = {
    "spec/1": ("goal", "why", "acceptance", "stage"), "batch/1": ("specs", "parallel", "order"),
    "release/1": ("specs", "repo", "branch", "sha", "tests"), "verify/1": ("release", "result", "evidence"),
    "incident/1": ("kind", "evidence", "cause"), "opinion/1": ("question", "agree", "disagree", "missing"),
    "ask/1": ("question",), "status/1": ("items",),
    "shadow/1": ("actor", "action", "rejected_by", "reason", "would_do"),
}
# a spec is WHAT, never HOW: these fields or phrases mean the sender is planning someone else's work
METHOD_FIELDS = {"steps", "plan", "how", "implementation", "files", "code", "patch", "approach", "method"}
METHOD_WORDS = re.compile(r"\b(implement by|step \d|first,? (write|edit|change)|edit the file|use the function|"
                          r"call [a-z_.]+\(|in [a-z_/]+\.py:\d+ (change|replace))", re.I)
STAGES = {"R0", "R1", "R2", "R3", "R4", "R5"}
SHADOW_SOURCES = {"guard", "sensor", "runtime", "budget", "policy"}  # ga-engine internal only; never a platform denial


class FlowError(ValueError):
    pass


def check(frm: str, to: str, form: str, msg: dict) -> None:
    if frm not in ROLES or to not in ROLES:
        raise FlowError(f"unknown role {frm}->{to}")
    if form not in EDGES.get((frm, to), set()):
        raise FlowError(f"{frm} may not send {form} to {to} (allowed: {sorted(EDGES.get((frm, to), set()))})")
    if not isinstance(msg.get("id"), str) or not msg["id"]:
        raise FlowError("id missing")
    miss = [k for k in REQUIRED[form] if k not in msg]
    if miss:
        raise FlowError(f"{form}: missing {miss}")
    specs = [msg] if form == "spec/1" else (msg.get("specs") if form == "batch/1" else [])
    for sp in specs:
        if not isinstance(sp, dict):
            raise FlowError("batch/1: specs must be spec/1 objects")
        bad = METHOD_FIELDS & set(sp)
        if bad:
            raise FlowError(f"spec {sp.get('id')}: method fields {sorted(bad)} — a spec says what, Dev/Ops decide how")
        text = json.dumps({k: sp.get(k) for k in ("goal", "acceptance", "constraints")}, ensure_ascii=False)
        if METHOD_WORDS.search(text):
            raise FlowError(f"spec {sp.get('id')}: reads like a method ('{METHOD_WORDS.search(text).group(0)}')")
        if sp.get("stage") not in STAGES:
            raise FlowError(f"spec {sp.get('id')}: stage must be one of {sorted(STAGES)}")
        if not isinstance(sp.get("acceptance"), list) or not sp["acceptance"]:
            raise FlowError(f"spec {sp.get('id')}: acceptance must be a non-empty list of checkable criteria")
    if form == "shadow/1" and msg.get("rejected_by") not in SHADOW_SOURCES:
        raise FlowError(f"shadow/1: rejected_by must be a ga-engine source {sorted(SHADOW_SOURCES)}; a platform permission denial is reported directly, not shadowed")
    if form == "batch/1":
        ids = {s["id"] for s in msg["specs"]}
        flat = [i for g in msg["parallel"] for i in g]
        if set(flat) != ids or set(msg["order"]) != ids:
            raise FlowError("batch/1: parallel groups and order must cover exactly the batch's spec ids")


def send(frm: str, to: str, form: str, msg: dict, root: Path = HERE) -> Path:
    check(frm, to, form, msg)
    now = datetime.now(KST)
    msg = {**msg, "form": form, "from": frm, "to": to, "at": now.isoformat(timespec="seconds")}
    d = root / "inbox" / to
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{now:%Y%m%dT%H%M%S}-{frm}-{form.replace('/', '')}-{msg['id']}.json"
    p.write_text(json.dumps(msg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return p


def inbox(role: str, since: str = "", root: Path = HERE) -> list[dict]:
    d = root / "inbox" / role
    return [json.loads(p.read_text()) for p in sorted(d.glob("*.json")) if p.name > since] if d.is_dir() else []


def _self_test() -> None:
    import tempfile
    r = Path(tempfile.mkdtemp())
    sp = {"id": "S1", "goal": "x", "why": "y", "acceptance": ["a"], "stage": "R0"}
    send("baseline", "dev", "spec/1", sp, r)
    for bad, why in [(("dev", "baseline", "spec/1", sp), "edge"), (("baseline", "dev", "spec/1", {**sp, "steps": [1]}), "method field"),
                     (("baseline", "dev", "spec/1", {**sp, "goal": "edit the file foo"}), "method words"),
                     (("baseline", "dev", "spec/1", {**sp, "stage": "R9"}), "stage"), (("ops", "baseline", "batch/1", {"id": "b"}), "edge2"),
                     (("ops", "dev", "batch/1", {"id": "b", "specs": [sp], "parallel": [["S1"]], "order": []}), "order")]:
        try:
            send(*bad, root=r)
        except FlowError:
            continue
        raise AssertionError(f"not rejected: {why}")
    send("ops", "dev", "batch/1", {"id": "B1", "specs": [sp], "parallel": [["S1"]], "order": ["S1"], "why": "w"}, r)
    assert len(inbox("dev", root=r)) == 2
    send("ops", "baseline", "shadow/1", {"id": "SH1", "actor": "ops", "action": "x", "rejected_by": "guard", "reason": "r", "would_do": "w"}, r)
    try:
        send("ops", "baseline", "shadow/1", {"id": "SH2", "actor": "ops", "action": "x", "rejected_by": "platform", "reason": "r", "would_do": "w"}, r)
        raise AssertionError("platform denial accepted as shadow")
    except FlowError:
        pass
    print("self-test ok")


def main(a: list[str]) -> int:
    if a[1:2] == ["--self-test"]:
        _self_test()
        return 0
    if a[1:2] == ["send"] and len(a) == 6:
        try:
            print(send(a[2], a[3], a[4], json.loads(Path(a[5]).read_text(encoding="utf-8"))))
        except FlowError as e:
            print(f"REJECTED: {e}", file=sys.stderr)
            return 2
        return 0
    if a[1:2] == ["inbox"]:
        since = a[a.index("--since") + 1] if "--since" in a else ""
        for m in inbox(a[2], since):
            print(json.dumps(m, ensure_ascii=False))
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
