"""flow judge (user 10-06): one deterministic decision for an action, the same in every session.

Why: the same INTEGRATE / shared-file change was allowed in one session and refused in the next, because each session
judged from its own context. This script judges from the action and the recorded policy only, and returns the reasons.
It is also the single gate of the VM bridge (ops/agy_bridge/gate.py): the bridge executes only on "allow".

    python3 ops/flow/judge.py <action.json>     -> one JSON decision on stdout; exit 0 allow, 2 deny, 3 conflict/human_review
    python3 ops/flow/judge.py --self-test

action.json:
  {"id", "kind": integrate | push | mail | session_create | agent_create | shared_write | policy_change | other,
   "repo", "branch", "sha", "files": [paths],            (integrate / push / mail)
   "directive", "content": "<hash>",                     (mail: which directive, which reply; part of the key)
   "verdict_id", "evidence": {"ff_or_clean_merge", "suites_green", "mutations_ok"},   (integrate)
   "target", "change",                                   (shared_write / policy_change: the path and what changes)
   "agent_type", "scope", "permissions": [...], "controller_permissions": [...], "max_runtime_s",
                                                         (session_create / agent_create)
   "refs": ["force push" | "PR" | "secrets" | "new credential" | ...],   (anything else the action touches)
   "approvals": [{"source": "user_direct" | "relayed", "via", "words", "grants": [kind...], "key"}],
   "features": {"removes_human_checkpoint", "agents_manage_agents", "permanent"},
   "usage": {"sessions", "children", "pushes", "retries"},   (counts before this action; the caller supplies them)
   "stop": bool,                                         (stop switch: no new work starts)
   "session": "<id>",                                    (recorded only; never changes the decision)
   "prior": [{"decision", "by": "flow" | "platform", "policy_sha", "reason"}]}

Five factors are judged separately and none decides alone: session_context, cross_session_approval, policy_file,
action_content, human_oversight.
  - session_context is recorded and ignored: the same action gives the same decision in any session.
  - a relayed approval (sent between sessions) counts when a rule in policy.json accepts relayed approval for that kind
    of action and the action is inside that rule's scope. A relayed approval that no rule covers does not count. It is
    reported as a note, not as a conflict, because there is nothing for it to conflict with.
  - policy.json missing, unreadable, corrupt, of an unknown schema, or failing its hash check -> deny (fail-closed).
    Readable, but no rule for this kind of action -> human_review: the user decides directly. (user 10-06)
  - inside a rule -> allow, with no per-action human step. Outside the rule's scope -> human_review. What a rule
    forbids ("never"), or a rule's condition that fails -> deny.
  - a shared file (assign.json ...) is not refused for being shared: it is refused only when a recorded rule protects it.
  - a standing rule that removes a human checkpoint, or lets agents create/manage/stop agents, is flagged human_review.
    Plain session creation or automation that a person still approves and controls is judged like any other action.
    A worker never gets more than its controller: permissions must be within both the rule and the controller's.
  - a change that touches the policy, the judge or the bridge gate is a policy change, whatever kind it was sent as.
  - limits (policy.json "limits", else LIMITS below): reaching one -> human_review.
  - when an approval and policy.json disagree: if policy.json has a "precedence" list, it decides. Otherwise the
    result is conflict, with both sides named.
  - a prior decision is checked against the current policy sha: under the same policy a prior deny / human_review /
    conflict stands (a reworded or re-routed attempt gets the same answer); a changed policy is judged again. A past
    approval never covers a new action by itself. The user's own approval of one action's key lifts human_review for
    that action only; it never lifts deny or the stop switch.

Scope: this judges the flow layer (should a session or the bridge attempt this). It does not and cannot change a
Claude Code / platform permission decision. A platform denial ends that attempt: report the exact text to the user, do
not reword and retry. The only cross-session fix for that is a permission rule the user adds themselves (HUMAN_QUEUE G).
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
POLICY = HERE / "policy.json"
VERDICTS = HERE.parent / "hub" / "baseline_verdicts.jsonl"
SCHEMAS = {"policy/1"}
KINDS = {"integrate", "push", "mail", "session_create", "agent_create", "shared_write", "policy_change", "other"}
EVIDENCE = ("ff_or_clean_merge", "suites_green", "mutations_ok")  # policy auto_integrate conditions 3-5
# policy.json "never" phrases -> the ref an action names when it touches one
NEVER_REFS = {"force push": "force push", "PRs": "PR", "secrets": "secrets", "model ids in commits": "model ids in commits",
              "any other ref": "other ref"}
# the policy, the judge and the bridge's own gate/executors: changing one is a policy change, never a plain push
PROTECTED = {"ops/flow/policy.json", "ops/flow/judge.py", "ops/agy_bridge/gate.py", "ops/agy_bridge/bridge.py",
             "ops/agy_bridge/act_runner.py", "ops/agy_bridge/tools.json", "ops/agy_bridge/agy_tools.py"}
LIMITS = {"max_sessions": 5, "max_children_per_session": 3, "max_runtime_s": 3600, "max_retries": 1, "max_pushes": 20}
RANK = {"allow": 0, "human_review": 1, "conflict": 2, "deny": 3}
KEY_FIELDS = ("kind", "repo", "branch", "sha", "files", "target", "change", "agent_type", "scope", "permissions",
              "directive", "content")


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:12] if p.is_file() else "none"


def _verdicts(p: Path) -> list[dict]:
    if not p.is_file():
        return []
    return [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]


def action_key(act: dict) -> str:
    """What the action does, not who sends it or how: the same outcome by another command, session or host has the
    same key. Session, approvals, usage, prior and wording are left out."""
    k = {f: act.get(f) for f in KEY_FIELDS if act.get(f) not in (None, "", [])}
    for f in ("files", "permissions"):
        if f in k:
            k[f] = sorted(k[f])
    return hashlib.sha256(json.dumps(k, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def load_policy(path: Path = POLICY, pinned: str | None = None) -> tuple[dict | None, str, str]:
    """(policy, sha, problem). policy is None when it must not be used: missing, unreadable, corrupt, unknown schema,
    or failing the hash check — the pinned sha when given, else the file must equal the committed version."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        return None, "none", f"policy.json missing or unreadable: {type(e).__name__}"
    sha = hashlib.sha256(raw).hexdigest()[:12]
    try:
        pol = json.loads(raw.decode("utf-8"))
    except ValueError:
        return None, sha, "policy.json is not valid JSON"
    if not isinstance(pol, dict) or pol.get("schema") not in SCHEMAS:
        return None, sha, f"policy.json schema {pol.get('schema') if isinstance(pol, dict) else '?'!r} not in {sorted(SCHEMAS)}"
    if pinned:
        if pinned != sha:
            return None, sha, f"policy.json sha {sha} != pinned {pinned}"
    else:
        p = subprocess.run(["git", "-C", str(path.parent), "show", f"HEAD:./{path.name}"], capture_output=True)
        if p.returncode != 0:
            return None, sha, "policy.json hash check failed: not committed and no pinned sha"
        if p.stdout != raw:
            return None, sha, "policy.json hash check failed: differs from the committed version"
    return pol, sha, ""


def _branch_ok(branch: str | None, allowed: list[str]) -> bool:
    """An entry ending in '/' is a prefix (agv/); any other entry is one exact branch."""
    return bool(branch) and any(branch.startswith(a) if a.endswith("/") else branch == a for a in allowed)


def judge(act: dict, policy: dict | None, verdicts: list[dict], policy_sha: str, problem: str = "") -> dict:
    key = action_key(act)
    if policy is None:  # missing or unusable: fail-closed
        return {"id": act.get("id"), "key": key, "decision": "deny", "policy_sha": policy_sha,
                "reasons": [{"factor": "policy_file", "decision": "deny",
                             "reason": (problem or "policy.json missing or unreadable") + ": fail-closed"}],
                "factors": {"session_context": {"session": act.get("session"), "used": False}}}
    if act.get("stop"):  # stop switch: nothing new starts, and no approval lifts it
        return {"id": act.get("id"), "key": key, "decision": "human_review", "policy_sha": policy_sha,
                "reasons": [{"factor": "human_oversight", "decision": "human_review",
                             "reason": "stop switch is on: no new push, session, agent or hand-off starts"}],
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
    br = policy.get("bridge", {}) or {}
    rules = {k: v for k, v in (("integrate", ai), ("push", br.get("push")), ("mail", br.get("mail")),
                               ("session_create", br.get("sessions")), ("agent_create", br.get("sessions"))) if v}
    never = [NEVER_REFS.get(n, n) for n in [*ai.get("never", []), *br.get("never", [])]]
    touched = sorted(set(act.get("refs", [])) & set(never))
    if touched:
        say("policy_file", "deny", f"policy.json never: {touched}")
    hit = sorted(set(act.get("files") or []) & PROTECTED) if act.get("repo") in (None, "cogito5170/baseline") else []
    if kind in ("shared_write", "policy_change") and act.get("target") in PROTECTED:
        hit = [act["target"]]
    if hit:
        say("policy_file", "human_review", f"touches the policy / judge / gate {hit}: a policy change, not a {kind}")
        kind = "policy_change"
    rule = rules.get(kind)
    if kind in ("integrate", "push", "mail", "session_create", "agent_create") and not rule:
        say("policy_file", "human_review", f"no {kind} rule in policy.json")
    elif kind == "integrate":
        want = rule.get("repos", {}).get(act.get("repo"))
        if want is None:
            say("policy_file", "human_review", f"repo {act.get('repo')} not in auto_integrate.repos")
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
        if not any(o[1] in ("deny", "human_review") for o in out):
            say("policy_file", "allow", f"inside auto_integrate (approved_by {rule.get('approved_by')}): repo, "
                                        "branch, ACCEPT verdict at this sha, conditions stated")
    elif kind in ("push", "mail"):
        allowed = rule.get(act.get("repo"))
        if allowed is None:
            say("policy_file", "human_review", f"repo {act.get('repo')} not in bridge.{kind}")
        elif not _branch_ok(act.get("branch"), allowed):
            say("policy_file", "human_review", f"branch {act.get('branch')} not in bridge.{kind}[{act.get('repo')}] {allowed}")
        if kind == "push" and not act.get("sha"):
            say("policy_file", "deny", "push without a sha")
        if not any(o[1] in ("deny", "human_review") for o in out):
            say("policy_file", "allow", f"inside bridge.{kind}: {act.get('repo')} {act.get('branch')}")
    elif kind in ("session_create", "agent_create"):
        want = set(act.get("permissions") or [])
        if act.get("agent_type") not in rule.get("agent_types", []):
            say("policy_file", "human_review", f"agent type {act.get('agent_type')!r} not in bridge.sessions.agent_types")
        if act.get("scope") not in rule.get("scopes", []):
            say("policy_file", "human_review", f"scope {act.get('scope')!r} not in bridge.sessions.scopes")
        if act.get("repo") and not _branch_ok(act.get("branch"), rule.get("repos", {}).get(act["repo"], [])):
            say("policy_file", "human_review", f"{act.get('repo')} {act.get('branch')} not in bridge.sessions.repos")
        if want - set(rule.get("permissions", [])):
            say("policy_file", "human_review", f"permissions {sorted(want - set(rule.get('permissions', [])))} beyond bridge.sessions")
        if "controller_permissions" not in act and kind == "agent_create":
            say("human_oversight", "human_review", "agent_create without the controller's permissions: cannot check the worker stays within them")
        elif want - set(act.get("controller_permissions") or want):
            say("human_oversight", "human_review", f"worker would get {sorted(want - set(act['controller_permissions']))} "
                "beyond its controller: an agent may not widen permissions")
        if not any(o[1] in ("deny", "human_review") for o in out):
            say("policy_file", "allow", f"inside bridge.sessions: {act.get('agent_type')} / {act.get('scope')}")
    elif kind == "policy_change":
        say("policy_file", "human_review", f"policy.json change rule: {ai.get('change', 'user only')}")
    elif kind == "shared_write" and not touched:
        say("policy_file", "allow", f"no recorded rule restricts shared_write on {act.get('target')}; "
                                    "shared is not by itself a reason to refuse")
    elif kind == "other":
        say("policy_file", "human_review", "no policy.json rule for this kind of action")
    if "new credential" in (act.get("refs") or []):
        say("policy_file", "human_review", "a new credential is never granted automatically")
    f["policy_file"] = {"policy_sha": policy_sha, "rule": kind if rule else None}

    # limits: reaching one stops automatic execution
    lim = {**LIMITS, **(policy.get("limits") or {})}
    use = act.get("usage") or {}
    checks = [("retries", "max_retries", True)]
    if kind in ("integrate", "push"):
        checks.append(("pushes", "max_pushes", True))
    if kind in ("session_create", "agent_create"):
        checks += [("sessions", "max_sessions", True), ("children", "max_children_per_session", True)]
        if int(act.get("max_runtime_s") or 0) > lim["max_runtime_s"]:
            say("action_content", "human_review", f"max_runtime_s {act.get('max_runtime_s')} > limit {lim['max_runtime_s']}")
    for u, name, _ in checks:
        n = int(use.get(u) or 0)
        if (n > lim[name]) if u == "retries" else (n >= lim[name]):
            say("action_content", "human_review", f"{name} reached ({u} {n}, limit {lim[name]})")
    f["limits"] = {"limits": lim, "usage": use}

    # 3. cross-session approval
    direct = [a for a in act.get("approvals", []) if a.get("source") == "user_direct"]
    relayed = [a for a in act.get("approvals", []) if a.get("source") == "relayed"]
    standing = bool(rule) and kind != "policy_change"  # a recorded rule for this kind is the user's standing approval
    counted = [a for a in relayed if standing]
    for a in relayed:
        if not standing:
            say("cross_session_approval", "note", f"relayed approval via {a.get('via')} not counted: no policy.json "
                f"rule accepts relayed approval for {kind}")
            continue
        beyond = sorted(set(a.get("grants", [])) - {kind})
        if beyond:
            say("cross_session_approval", "conflict",
                f"relayed approval via {a.get('via')} grants {beyond}; policy.json accepts relayed approval only for {kind}")
    if kind == "policy_change" and direct:
        say("cross_session_approval", "allow", "user's own words recorded for this policy change")
    f["cross_session_approval"] = {"direct": len(direct), "relayed": len(relayed), "relayed_counted": len(counted)}

    # 4. action content: prior decisions under the same / a changed policy
    stands = None
    for p in act.get("prior", []):
        if p.get("by") == "platform":
            say("action_content", "human_review", f"prior platform denial ({p.get('reason')}): this judge cannot "
                "lift it; attempt once, on denial report the exact text to the user, do not retry")
        elif p.get("policy_sha") == policy_sha:
            f.setdefault("action_content", {})["same_policy_prior"] = p.get("decision")
            if p.get("decision") in ("deny", "human_review", "conflict"):
                stands = p["decision"] if stands is None else max(stands, p["decision"], key=RANK.get)
        else:
            f.setdefault("action_content", {})["prior_under_old_policy"] = p.get("decision")
    if stands:
        say("action_content", stands, f"same action, same policy: the prior {stands} stands (no retry by another "
            "command, session, agent or host)")
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
    elif decision == "human_review" and not standing_autonomy and any(a.get("key") == key for a in direct):
        decision = "allow"  # the user approved exactly this action (never lifts deny, conflict or the stop switch)
        out.append(("cross_session_approval", "allow", f"user's own approval of this action ({key})"))
    return {"id": act.get("id"), "key": key, "decision": decision, "policy_sha": policy_sha,
            "reasons": [{"factor": a, "decision": b, "reason": c} for a, b, c in out], "factors": f}


def run(path: Path, policy_path: Path = POLICY, pinned: str | None = None) -> dict:
    act = json.loads(path.read_text(encoding="utf-8"))
    pol, sha, problem = load_policy(policy_path, pinned)
    return judge(act, pol, _verdicts(VERDICTS), sha, problem)


def _self_test() -> None:
    import tempfile
    pol = json.loads(POLICY.read_text(encoding="utf-8"))
    ver = [{"id": "DEV-R0a", "sha": "759d873", "decision": "ACCEPT"}, {"id": "X", "decision": "SEND_BACK"}]
    ok_ev = {k: True for k in EVIDENCE}
    integ = {"id": "I1", "kind": "integrate", "repo": "cogito5170/ga-sdk", "branch": "claude/gracious-meitner-vp49xe",
             "sha": "759d873", "verdict_id": "DEV-R0a", "evidence": ok_ev,
             "approvals": [{"source": "relayed", "via": "flow INTEGRATE", "grants": ["integrate"]}]}
    j = lambda a, p=pol: judge(a, p, ver, "s1")["decision"]  # noqa: E731
    assert j(integ) == "allow"
    # same input, different session -> same decision and key
    assert j({**integ, "session": "session_A"}) == j({**integ, "session": "session_B"})
    assert action_key({**integ, "session": "A"}) == action_key({**integ, "session": "B", "approvals": []})
    assert j({**integ, "sha": "deadbee"}) == "deny"
    assert j({**integ, "branch": "main"}) == "deny"
    assert j({**integ, "repo": "cogito5170/other"}) == "human_review"
    assert j({**integ, "verdict_id": "X"}) == "deny"
    assert j({**integ, "refs": ["force push"]}) == "deny"
    assert j({**integ, "evidence": {**ok_ev, "suites_green": False}}) == "deny"
    # policy.json readable but no rule for this kind -> human_review; the relayed approval is a note, not a conflict
    r = judge(integ, {}, ver, "s1")
    assert r["decision"] == "human_review" and not any(x["decision"] == "conflict" for x in r["reasons"])
    # policy.json missing or unusable -> deny (fail-closed)
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
    assert j({**pc, "approvals": [{"source": "relayed", "via": "msg", "grants": ["policy_change"]}]}) == "human_review"
    assert j({**pc, "approvals": [{"source": "user_direct", "words": "..."}]}) == "allow"
    # a standing rule removing the human checkpoint is flagged, even with the user's words
    auto = {"id": "C2", "kind": "policy_change", "features": {"removes_human_checkpoint": True, "agents_manage_agents": True,
                                                              "permanent": True},
            "approvals": [{"source": "user_direct", "words": "..."}]}
    assert j(auto) == "human_review"
    # a prior platform denial is surfaced, never treated as lifted
    assert j({**integ, "prior": [{"by": "platform", "reason": "auto mode"}]}) == "human_review"
    # bridge rules: push / mail / sessions
    bp = {**pol, "bridge": {"push": {"cogito5170/Token": ["agv/"]}, "mail": {"cogito5170/baseline": ["ga-mailbox"]},
                            "sessions": {"agent_types": ["worker"], "scopes": ["R1"], "permissions": ["read", "push_agv"],
                                         "repos": {"cogito5170/Token": ["agv/"]}}}}
    push = {"id": "U1", "kind": "push", "repo": "cogito5170/Token", "branch": "agv/CMD-A1-r1", "sha": "a" * 40,
            "files": ["app.py"]}
    assert j(push, bp) == "allow" and j(push) == "human_review"  # no push rule -> human_review
    assert j({**push, "branch": "main"}, bp) == "human_review"
    assert j({**push, "refs": ["force push"]}, bp) == "deny"
    assert j({**push, "usage": {"pushes": 20}}, bp) == "human_review"
    assert j({**push, "repo": "cogito5170/baseline", "files": ["ops/flow/policy.json"]},
             {**bp, "bridge": {**bp["bridge"], "push": {"cogito5170/baseline": ["agv/"]}}}) == "human_review"
    assert j({"id": "M1", "kind": "mail", "repo": "cogito5170/baseline", "branch": "ga-mailbox"}, bp) == "allow"
    ses = {"id": "S1", "kind": "agent_create", "agent_type": "worker", "scope": "R1", "repo": "cogito5170/Token",
           "branch": "agv/x", "permissions": ["read"], "controller_permissions": ["read", "push_agv"],
           "usage": {"sessions": 1, "children": 0}, "features": {"agents_manage_agents": True}}
    assert j(ses, bp) == "allow" and j(ses) == "human_review"
    assert j({**ses, "permissions": ["read", "push_agv"], "controller_permissions": ["read"]}, bp) == "human_review"
    assert j({**ses, "permissions": ["admin"]}, bp) == "human_review"
    assert j({**ses, "usage": {"sessions": 5}}, bp) == "human_review"
    assert j({**ses, "refs": ["new credential"]}, bp) == "human_review"
    assert j({"id": "O1", "kind": "other"}) == "human_review"
    # prior under the same policy stands; a changed policy is judged again; the user's key approval lifts human_review only
    out_of_scope = {**push, "branch": "main"}
    k = action_key(out_of_scope)
    assert j({**out_of_scope, "approvals": [{"source": "user_direct", "key": k}]}, bp) == "allow"
    assert j({**push, "refs": ["force push"], "approvals": [{"source": "user_direct", "key": action_key(push)}]}, bp) == "deny"
    assert j({**push, "prior": [{"by": "flow", "decision": "deny", "policy_sha": "s1"}]}, bp) == "deny"
    assert j({**push, "prior": [{"by": "flow", "decision": "deny", "policy_sha": "old"}]}, bp) == "allow"
    assert j({**push, "stop": True, "approvals": [{"source": "user_direct", "key": action_key(push)}]}, bp) == "human_review"
    # load_policy: pinned sha, corrupt, unknown schema, missing
    d = Path(tempfile.mkdtemp())
    (d / "p.json").write_text(json.dumps({"schema": "policy/1"}))
    good = _sha(d / "p.json")
    assert load_policy(d / "p.json", good)[0] == {"schema": "policy/1"}
    assert load_policy(d / "p.json", "0" * 12)[0] is None
    assert load_policy(d / "p.json")[0] is None  # not committed, no pin
    (d / "c.json").write_text("{not json")
    (d / "v.json").write_text(json.dumps({"schema": "policy/9"}))
    assert load_policy(d / "c.json", "x")[0] is None and load_policy(d / "v.json", _sha(d / "v.json"))[0] is None
    assert load_policy(d / "none.json", "x")[0] is None
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
