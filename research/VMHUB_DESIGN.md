# VMHUB rev3 design — VM Ops core, gates, gateway budget (Dev, for review)

Status: DESIGN ONLY. Build is ON HOLD (DEV-VMHUB rev3, DEV-VMBUDGET): it starts only after the user confirms from
measurements that the token problem is solved, and after R0-baseline exists. Until a later cutover spec the cloud
Dev/Ops hubs stay the authority and the VM acts only in shadow (VM-owned shadow refs, no externally visible action).
Author: Dev hub session_01VMbRhMjtfPAALfLjAWJ1tT, 10-07 01:xx KST. Review: Ops opinion/1 before any build request.
Code refs are ga-sdk @ 277945de (`ga/...`).

## 0. Starting point (what exists, facts)

| need | exists today | gap |
|---|---|---|
| deterministic verdict | `ga/judge.py` `judge()` :365 (fresh clone, net-blocked tests, seeded mutations, class + needs), no model | none for the verdict itself |
| integrate push | `judge.apply` :726-743 (success + needs empty + ff, no force); `adapters/git.py` `fast_forward` :273 with PRE_RECEIVE hook (R3) | hub decision before it is a model turn |
| hub decision | `MailHub._decide` hub.py:1844 → `run_turn` :1856 (model answers ACCEPT/SEND_BACK/ASK_HUMAN, then deterministic overrides :1771-1783) | model call on the integration path (DEV-R3-DET removes it) |
| rules / gates | `ga/rules.py` R1-R13 (r3_push :89, r12_budget :212), `ga/gates.py` Gate 1-7 :17-25, deterministic | no commit gate / push gate split; no session caps |
| metering | hub ledger `~/.ga/hub/ledger/<date>.jsonl` (tokens, served, card_bytes); `net/usage.py`; `backends/catalog.py` prices :29-33; `rlo.governor` rpm/tpm | not one gateway; USD caps not enforced per call |
| model call sites | hub.py:1662, plan/cli.py:59, act/loop.py:626,674, gemini.py:246,637, net/node.py:379,469; subprocess claude/agy/gemini adapters; agent_sdk.py:138; backends/http.py:33 | 6+ direct sites → one gateway |
| sessions | none on the VM (create_session is a denied tool, rlo/remote.py) | session manager is new |
| VM loop | systemd: ga-hub.timer 60 s (`ga hub tick --shadow`), ga-update.timer 30 min (ff-only, `_notice` per version) | SHA report (DEV-VMSHA) |

## 1. Components

```
 cloud (flow boundary: spec/1 ask/1 in; status/1 opinion/1 incident/1 shadow/1 out)
   │
 ┌─┴──────────────────────── VM ─────────────────────────────────────────────┐
 │ Boundary (inbox/outbox)  ── admits only registry forms, dedups by id, ref   │
 │ Ops core (deterministic, no model)                                          │
 │   ├─ Planner/rules: spec → work items (needs_judgment only when no rule)    │
 │   ├─ Session manager: create/end worker sessions within caps                │
 │   ├─ Commit gate: per commit, from tests/paths/branch/diff/policy           │
 │   ├─ Push gate: per push, stricter (ref allowed, verdict, revert proven)    │
 │   └─ Gateway (DEV-VMAUTO): the ONLY model call path, budget check per call  │
 │ Workers (sandboxed): edit, test, commit; push impossible                    │
 │ State store: append-only journal + snapshots (replay = same decisions)      │
 └────────────────────────────────────────────────────────────────────────────┘
```

### 1.1 Gateway (R1; DEV-VMAUTO + DEV-VMBUDGET)
- One function `ga.llm.call(card, purpose, item_id, model_hint)`; every existing site (§0) is rewired to it; a test
  greps the package for `backends.create(` / `run_turn(` / subprocess model CLIs outside `ga/llm` and fails.
- Before the call: estimate USD = price(model) × (card tokens + max_output); check **every** cap in
  `ops/flow/policy.json vm_budget.caps` against the journal's spend windows; tightest applicable cap wins:
  `vm_coordination_dev_plus_ops_usd_per_h` (purpose in {coordination}), `vm_baselines_usd_per_h`
  (purpose in {coordination, intake, diagnosis, opinion}), `vm_total_usd_per_h`, `vm_total_usd_per_day`,
  `build_per_item_usd.default` (soft: needs_judgment to continue) and `.hard` (refuse).
- Over any cap → no call; `shadow/1 {rejected_by: budget, reason: <cap name, window spend, estimate>, would_do}`
  via ops/hub/shadow_digest.py stage; the item waits (fail-closed).
- After the call: record served model, input/output/cache tokens, USD (actual), card size, purpose, item_id,
  evidence fingerprint. Repeated judgment on the same fingerprint → rule cache entry → 0 calls next time.
- Values are read from policy.json at each call (no constants); a policy change takes effect without a code change.
- Card only (role + evidence, fixed max size); no conversation history; context size recorded.

### 1.2 Session manager
- States: `requested → admitted | refused → running → (committed)* → ended(done|timeout|budget|error)`.
- Admission checks (policy `vm_policy`, user-owned): max concurrent sessions, max child sessions per item,
  total session budget/day, session timeout, one session per work item (dedup by item id), item budget (§1.1).
  Refusal → shadow/1 `rejected_by: policy|budget`.
- A session is a sandboxed worker process (headless adapter) in its own worktree with PRE_PUSH hook that rejects
  every push and no push credential in its environment; model calls only through the gateway.
- End: on done, timeout, budget stop (net/checkpoint budget_stop = checkpoint, not failure) or error; the
  worktree and its commits stay for the gates; journal records the end reason.

### 1.3 Commit gate (inside the VM; "VM-internal state")
- Input: worktree commit, item spec (allowed paths, target branch), tests to run, policy.
- Checks (deterministic): paths ⊆ allowed; target = the item's work branch; acceptance test identical to the
  spec's and red on base; full suite green in the reference env (refenv); secrets scan (r6); diff size within item.
- Output per commit: `{sha, decision: pass|fail, evidence: {tests, paths, diff_stat}, rule ids}` → journal.
- Zero model calls (test enforces).

### 1.4 Push gate (higher authority; "publishing outside")
- Input: a commit-gate-passed sha, target repo/ref, policy.
- Checks: repo/ref in `vm_policy.push_allowed` (until cutover: VM shadow refs only, e.g. `vm-shadow/<ref>`);
  `judge()` class success, needs empty; seeded mutations killed (or cross-covered and recorded); revert proven
  (revert makes the acceptance test fail); ff or clean merge; no force/delete (R3, PRE_RECEIVE).
- Only the Ops core holds the push credential; push via `GitVcs.fast_forward`; each push → status/1 to cloud
  `{sha, ref, gate evidence}`.

### 1.5 Boundary and state
- Forms from the single registry (DEV-FORMATS); id = request identity, ref = answered id; duplicate id answered once.
- Journal: append-only JSONL (inputs, decisions, gateway calls); state = fold(journal); restart replays to the
  same state; outbox sends are idempotent by id (no lost/duplicated message).

## 2. Policy fields read (all user-owned, never written by VM code)

| file / key | read by |
|---|---|
| `policy.json vm_budget.caps.*` | gateway (every call) |
| `policy.json vm_budget.model` | gateway model choice (cheapest that passes; Opus only opinion/diagnosis) |
| `policy.json vm_policy.sessions{max_concurrent,max_children,timeout_s,per_day_usd}` (new, user to set) | session manager |
| `policy.json vm_policy.push_allowed[{repo,ref}]` (new; shadow refs until cutover) | push gate |
| `policy.json auto_integrate.conditions/never` | push gate |
| `watch_thresholds.json` (Ops) | DEV-WATCH, not the gates |

A write to these keys from anything but a user-signed commit on the baseline branch is rejected and recorded
(the VM verifies the commit author/hash against the last user-approved policy hash it was given at the boundary).

## 3. Failure and rollback

| failure | behaviour |
|---|---|
| over budget / over cap | refuse, shadow/1, item waits; never retried automatically within the window |
| gateway/model error | label (served-model mismatch, timeout, refusal) recorded; item → needs_judgment once, then ASK (status/1) |
| commit gate fail | session gets the evidence card once (budgeted), else item ends `fail` and is reported |
| push gate fail | no push; status/1 with the failed check; nothing outside the VM changes |
| bad push already made (shadow ref) | revert commit on the same ref (never force); cloud informed by status/1 |
| VM restart | replay journal; outbox resends unacked ids; sessions marked `ended(error)` and re-admitted by rule |
| policy file missing/invalid | fail-closed: no model call, no session, no push; incident/1 to cloud |
| kill switch | user-only flag outside the VM's control (systemd unit disable / a policy key the VM cannot write) stops all |

## 4. Acceptance map (DEV-VMHUB rev3 → part)

| acceptance line | part |
|---|---|
| rev2 rules (boundary forms, id/ref, no cloud read of VM internals, replay, restart, new form version) | §1.5 |
| worker can commit, any push fails; only Ops core pushes after both gates | §1.2 (PRE_PUSH reject, no credential), §1.4 |
| commit gate from tests/paths/branch/diff/policy, 0 model calls, recorded per commit | §1.3 |
| push gate separate and higher; status/1 per push naming sha and ref | §1.4 |
| Ops core creates/ends sessions within caps; over cap refused as shadow/1 | §1.2 |
| every VM model call via the single gateway | §1.1 |
| DEV-VMBUDGET: every call checked against all caps, refused + shadow/1; a test per cap | §1.1 (tests: one per cap at limit and limit+ε) |

## 5. Order (after R0-baseline; build items stay held where marked)
1. R1 gateway + budgets (DEV-VMAUTO, DEV-VMBUDGET) — not held.
2. DEV-R3-DET (remove the model from `_decide`) — not held.
3. Session manager, commit gate, push gate — HELD (VMHUB rev3).
4. Boundary/registry (DEV-FORMATS) — not held.

## 6. Open questions for Ops / user
- `vm_policy.sessions` and `push_allowed` values (user).
- Where the user's kill switch lives (Ops).
- Model credential on the VM (user; status/1 blocker when R1 needs it).
