"""flow judge (user 10-06): one deterministic decision for an action, the same in every session.

Why: the same INTEGRATE / shared-file change was allowed in one session and refused in the next, because each session
judged from its own context. This script judges from the action and the recorded policy only, and returns the reasons.

    python3 ops/flow/judge.py <action.json>     -> one JSON decision on stdout; exit 0 allow, 2 deny, 3 conflict/human_review
    python3 ops/flow/judge.py --self-test

action.json:
  {"id", "kind": integrate | shared_write | policy_change | session_create | other,
   "repo", "branch", "sha", "verdict_id",               (integrate)
   "target", "change",                                   (shared_write / policy_change: the path and what changes)
   "evidence": {"ff_or_clean_merge", "suites_green", "mutations_ok"},   (integrate; the integrator checks, then states)
   "refs": ["force push" | "PR" | "secrets" | ...],      (anything else the action touches)
   "approvals": [{"source": "user_direct" | "relayed", "via", "words", "grants": [kind...]}],
   "features": {"removes_human_checkpoint", "agents_manage_agents", "permanent"},
   "session": "<id>",                                    (recorded only; never changes the decision)
   "prior": [{"decision", "by": "flow" | "platform", "policy_sha", "reason"}]}

Five factors are judged separately and none decides alone: session_context, cross_session_approval, policy_file,
action_content, human_oversight.
  - session_context is recorded and ignored: the same action gives the same decision in any session.
  - a relayed approval (sent between sessions) counts when a rule in policy.json accepts relayed approval for that kind
    of action and the action is inside that rule's scope. A relayed approval that no rule covers does not count. It is
    reported as a note, not as a conflict, because there is nothing for it to conflict with.
  - policy.json missing or unreadable -> deny (fail-closed: may be a broken checkout). Readable, but no rule for this
    kind of action -> human_review: the user decides directly. (user 10-06, "split by case")
  - a shared file (assign.json ...) is not refused for being shared: it is refused only when a recorded rule protects it.
  - a standing rule that removes a human checkpoint, or lets agents create/manage/stop agents, is flagged human_review.
    Plain session creation or automation that a person still approves and controls is judged like any other action.
  - when an approval and policy.json disagree: if policy.json has a "precedence" list, it decides. Otherwise the
    result is conflict, with both sides named.
  - a prior decision is checked against the current policy sha: same policy means the same decision is expected; a
    changed policy means judge again (the prior is not repeated). A past approval never covers a new action by itself.

Scope: this judges the flow layer (should a session attempt and send this). It does not and cannot change a Claude
Code / platform permission decision. A platform denial ends that attempt: report the exact text to the user, do not
reword and retry. The only cross-session fix for that is a permission rule the user adds themselves (HUMAN_QUEUE G).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
POLICY = HERE / "policy.json"
VERDICTS = HERE.parent / "hub" / "baseline_verdicts.jsonl"
KINDS = {"integrate", "shared_write", "policy_change", "session_create", "other"}
EVIDENCE = ("ff_or_clean_merge", "suites_green", "mutations_ok")  # policy auto_integrate conditions 3-5
# policy.json "never" phrases -> the ref an action names when it touches one
NEVER_REFS = {"force push": "force push", "PRs": "PR", "secrets": "secrets", "model ids in commits": "model ids in commits",
              "any other ref": "other ref"}
PROTECTED = {"ops/flow/policy.json"}  # its own "change" rule protects it; other shared files only by a recorded rule
RANK = {"allow": 0, "human_review": 1, "conflict": 2, "deny": 3}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:12] if p.is_file() else "none"


def _verdicts(p: Path) -> list[dict]:
    if not p.is_file():
        return []
    return [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]


def judge(act: dict, policy: dict | None, verdicts: list[dict], policy_sha: str) -> dict:
    if policy is None:  # missing or unreadable: fail-closed
        return {"id": act.get("id"), "decision": "deny", "policy_sha": policy_sha,
                "reasons": [{"factor": "policy_file", "decision": "deny",
                             "reason": "policy.json missing or unreadable: fail-closed"}],
                "factors": {"session_context": {"session": act.get("session"), "used": False}}}
    kind = act.get("kind") if act.get("kind") in KINDS else "other"
    f: dict[str, dict] = {}
    out: list[tuple[str, str, str]] = []  # (factor, decision, reason)

    def say(factor: str, decision: str, reason: str) -> None:
        out.append((factor, decision, reason))

    # 1. session context: recorded, never decisive
    f["session_context"] = {"session": act.get("session"), "used": False}

    # 2. policy file
    ai = policy.get("auto_integrate", {})
    rules = {"integrate": ai} if ai else {}
    rule = rules.get(kind)
    never = [NEVER_REFS.get(n, n) for n in ai.get("never", [])]
    touched = sorted(set(act.get("refs", [])) & set(never))
    if touched:
        say("policy_file", "deny", f"policy.json never: {touched}")
    if kind == "integrate":
        if not rule:
            say("policy_file", "human_review", "no integrate rule in policy.json")
        else:
            want = rule.get("repos", {}).get(act.get("repo"))
            if want is None:
                say("policy_file", "deny", f"repo {act.get('repo')} not in auto_integrate.repos")
            elif act.get("branch") != want:
                say("policy_file", "deny", f"branch {act.get('branch')} is not the integration branch {want} (any other ref: never)")
            v = [x for x in verdicts if x.get("id") == act.get("verdict_id")]
            last = v[-1] if v else None
            if not last or last.get("decision") != "ACCEPT":
                say("policy_file", "deny", f"no ACCEPT verdict recorded for {act.get('verdict_id')}")
            elif last.get("sha") and last["sha"] != act.get("sha"):
                say("policy_file", "deny", f"verdict ACCEPT is for {last['sha']}, action sha is {act.get('sha')}")
            miss = [k for k in EVIDENCE if (act.get("evidence") or {}).get(k) is not True]
            if miss:
                say("policy_file", "deny", f"auto_integrate conditions not stated true: {miss}")
            if not any(o[1] == "deny" for o in out):
                say("policy_file", "allow", f"inside auto_integrate (approved_by {rule.get('approved_by')}): repo, "
                                            "branch, ACCEPT verdict at this sha, conditions stated")
    if kind in ("shared_write", "policy_change") and act.get("target") in PROTECTED:
        kind = "policy_change"
    if kind == "policy_change":
        say("policy_file", "human_review", f"policy.json change rule: {ai.get('change', 'user only')}")
    if kind in ("shared_write", "session_create", "other") and not touched:
        say("policy_file", "allow", f"no recorded rule restricts {kind} on {act.get('target') or act.get('id')}; "
                                    "shared or automated is not by itself a reason to refuse")
    f["policy_file"] = {"policy_sha": policy_sha, "rule": "auto_integrate" if rule else None}

    # 3. cross-session approval
    direct = [a for a in act.get("approvals", []) if a.get("source") == "user_direct"]
    relayed = [a for a in act.get("approvals", []) if a.get("source") == "relayed"]
    standing = bool(rule) and kind == "integrate"  # auto_integrate: an INTEGRATE through the flow is the user's approval
    counted = [a for a in relayed if standing]
    for a in relayed:
        if not standing:
            say("cross_session_approval", "note", f"relayed approval via {a.get('via')} not counted: no policy.json "
                f"rule accepts relayed approval for {kind}")
            continue
        beyond = sorted(set(a.get("grants", [])) - {"integrate"})
        if beyond:
            say("cross_session_approval", "conflict",
                f"relayed approval via {a.get('via')} grants {beyond}; policy.json accepts relayed approval only for "
                "integrate")
    if kind == "policy_change" and direct:
        say("cross_session_approval", "allow", "user's own words recorded for this policy change")
    f["cross_session_approval"] = {"direct": len(direct), "relayed": len(relayed), "relayed_counted": len(counted)}

    # 4. action content: prior decisions under the same / a changed policy
    for p in act.get("prior", []):
        if p.get("by") == "platform":
            say("action_content", "human_review", f"prior platform denial ({p.get('reason')}): this judge cannot "
                "lift it; attempt once, on denial report the exact text to the user, do not retry")
        elif p.get("policy_sha") == policy_sha:
            f.setdefault("action_content", {})["same_policy_prior"] = p.get("decision")
        else:
            f.setdefault("action_content", {})["prior_under_old_policy"] = p.get("decision")
    f.setdefault("action_content", {})["kind"] = kind

    # 5. human oversight
    ft = act.get("features") or {}
    standing_autonomy = ft.get("removes_human_checkpoint") and (ft.get("permanent") or kind == "policy_change")
    if standing_autonomy or (ft.get("agents_manage_agents") and ft.get("permanent")):
        say("human_oversight", "human_review", "makes removing a human checkpoint / agents managing agents a standing "
            "rule: safety review by the user; no relayed approval covers it")
    f["human_oversight"] = {k: bool(ft.get(k)) for k in ("removes_human_checkpoint", "agents_manage_agents", "permanent")}

    # combine: worst factor wins, except a conflict that a recorded precedence resolves
    prec = policy.get("precedence")
    if prec:
        conflicts = [o for o in out if o[1] == "conflict"]
        out = [o for o in out if o[1] != "conflict"]
        out += [(c[0], "deny" if prec.index("policy_file") < prec.index("cross_session_approval") else "allow",
                 c[2] + f" -> precedence {prec}") for c in conflicts]
    decision = max((o[1] for o in out if o[1] in RANK), key=RANK.get, default="human_review")  # notes never decide
    if kind == "policy_change" and direct and not any(o[1] == "deny" for o in out) and not standing_autonomy:
        decision = "allow"  # the change rule's own condition met
    return {"id": act.get("id"), "decision": decision, "policy_sha": policy_sha,
            "reasons": [{"factor": a, "decision": b, "reason": c} for a, b, c in out], "factors": f}


def run(path: Path) -> dict:
    act = json.loads(path.read_text(encoding="utf-8"))
    try:
        pol = json.loads(POLICY.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pol = None
    return judge(act, pol if isinstance(pol, dict) else None, _verdicts(VERDICTS), _sha(POLICY))


def _self_test() -> None:
    pol = json.loads(POLICY.read_text(encoding="utf-8"))
    ver = [{"id": "DEV-R0a", "sha": "759d873", "decision": "ACCEPT"}, {"id": "X", "decision": "SEND_BACK"}]
    ok_ev = {k: True for k in EVIDENCE}
    integ = {"id": "I1", "kind": "integrate", "repo": "cogito5170/ga-sdk", "branch": "claude/gracious-meitner-vp49xe",
             "sha": "759d873", "verdict_id": "DEV-R0a", "evidence": ok_ev,
             "approvals": [{"source": "relayed", "via": "flow INTEGRATE", "grants": ["integrate"]}]}
    j = lambda a, p=pol: judge(a, p, ver, "s1")["decision"]  # noqa: E731
    assert j(integ) == "allow"
    # same input, different session -> same decision
    assert j({**integ, "session": "session_A"}) == j({**integ, "session": "session_B"})
    assert j({**integ, "sha": "deadbee"}) == "deny"
    assert j({**integ, "branch": "main"}) == "deny"
    assert j({**integ, "verdict_id": "X"}) == "deny"
    assert j({**integ, "refs": ["force push"]}) == "deny"
    assert j({**integ, "evidence": {**ok_ev, "suites_green": False}}) == "deny"
    # no standing rule -> a relayed approval is not counted
    # policy.json readable but no rule for this kind -> human_review; the relayed approval is a note, not a conflict
    r = judge(integ, {}, ver, "s1")
    assert r["decision"] == "human_review" and not any(x["decision"] == "conflict" for x in r["reasons"])
    # policy.json missing or unreadable -> deny (fail-closed)
    assert j(integ, None) == "deny"
    # an uncovered relayed approval does not escalate an action that needs none
    assert j({"id": "W2", "kind": "shared_write", "target": "ops/flow/assign.json",
              "approvals": [{"source": "relayed", "via": "msg", "grants": ["shared_write"]}]}) == "allow"
    # relayed approval claiming more than policy accepts -> conflict, named
    over = {**integ, "approvals": [{"source": "relayed", "via": "msg", "grants": ["integrate", "policy_change"]}]}
    assert j(over) == "conflict"
    assert j(over, {**pol, "precedence": ["policy_file", "cross_session_approval"]}) == "deny"
    # shared file: judged on content, not refused for being shared
    assert j({"id": "W1", "kind": "shared_write", "target": "ops/flow/assign.json", "change": {"dev.sessions.x": "s"}}) == "allow"
    # policy.json: user's own words required; a relayed approval is not enough
    pc = {"id": "P1", "kind": "shared_write", "target": "ops/flow/policy.json", "change": {}}
    assert j({**pc, "approvals": [{"source": "relayed", "via": "msg", "grants": ["policy_change"]}]}) in ("conflict", "human_review")
    assert j({**pc, "approvals": [{"source": "user_direct", "words": "..."}]}) == "allow"
    # plain session creation is fine; a standing rule removing the human checkpoint is flagged
    assert j({"id": "C1", "kind": "session_create", "features": {"agents_manage_agents": True}}) == "allow"
    auto = {"id": "C2", "kind": "policy_change", "features": {"removes_human_checkpoint": True, "agents_manage_agents": True,
                                                              "permanent": True},
            "approvals": [{"source": "user_direct", "words": "..."}]}
    assert j(auto) == "human_review"
    # a prior platform denial is surfaced, never treated as lifted
    assert j({**integ, "prior": [{"by": "platform", "reason": "auto mode"}]}) == "human_review"
    print("self-test ok")


def main(a: list[str]) -> int:
    if a[1:2] == ["--self-test"]:
        _self_test()
        return 0
    if len(a) == 2:
        r = run(Path(a[1]))
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return {"allow": 0, "deny": 2}.get(r["decision"], 3)
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
