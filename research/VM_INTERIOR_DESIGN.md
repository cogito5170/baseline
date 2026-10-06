# VM interior design: the whole planned VM (Dev, for Ops opinion/1)

Spec: DEV-VMDESIGN (R4). Status: DESIGN ONLY. This doc follows on from `research/VMHUB_DESIGN.md` r2 (Ops core:
gateway, session manager, commit/push gates, policy, kill switch), which stays valid and is only summarized in §8. It
also uses `research/R1R2_DESIGN.md` r3 (R1 gateway, R2 verdict dry-run) and `research/GA_ENGINE_RUNTIME.md` §4C/§4D
(state machine, workers, scheduler, ladder).
Author: Dev hub session_01VMbRhMjtfPAALfLjAWJ1tT, 10-07 01:xx KST.
Code refs: ga-sdk @ 277945d (local checkout; R0-baseline 8ead789, integration head 318b22a not fetched here; line
numbers may shift by a few lines).

These rules hold in every section:
- **Never two primaries.** The cloud Dev/Ops hubs stay the authority until a separate cutover spec. Until then the
  VM acts in shadow only: it pushes only to VM-owned shadow refs, and nothing it does is visible outside.
- **LLM output is a proposal.** Every transition, admission, commit, push and schedule decision is a deterministic
  function of recorded inputs.
- **VMHUB build stays HELD** (session manager, commit gate, push gate, Dev/Ops repos). R1/R2/WATCH/FORMATS/VMSHA continue.
- **Values come from policy files and are read when used.** This doc names the keys; values it does not know are
  listed in §13.

## 0. Policy sources (who owns each value)

| file | owner | read by | enforcing copy on VM |
|---|---|---|---|
| `policy.json vm_budget.*` (caps, applies, windows, model) | user | gateway | `/etc/ga/vm_policy.json` (root, 0644); baseline file is a hash-compared mirror |
| `policy.json vm_policy.sessions/push_allowed` | user | session manager, push gate | same |
| `policy.json vm_policy.deadlines/ladder/scheduler` (new, §2, §5, §6) | user | state machine, ladder, scheduler | same |
| `policy.json auto_integrate` | user | push gate (after cutover) | same |
| `ops/hub/watch_thresholds.json` | Ops | watcher (DEV-WATCH) | mirror in cogito5170/Ops `limits/` |
| `slo.json` (new, §4.4) | Ops (proposed, §13 Q4) | Ops worker, scheduler | cogito5170/Ops `limits/slo.json` |
| forms registry (DEV-FORMATS) | Dev (a registry change goes through a release) | every channel | installed ga-sdk package |

If the enforcing policy is missing, unreadable, or has `halt: true`, the VM halts: no model call, no dispatch, no
push (VMHUB_DESIGN §2-§3).

## 1. Boundary and registry (DEV-FORMATS, DEV-VMHUB rev2)

**One registry.** `ga/forms/registry.json` in ga-sdk is the single source. `ga.forms` reads it. Baseline `flow.py`
reads a vendored copy whose sha256 is checked against ga-sdk in a test, so the two cannot drift. Docs are generated
from the registry. Today the forms are split: `flow.py` EDGES/REQUIRED at flow.py:38-51, and ga.forms `NOTIFY_KINDS`
at kinds.py:125, which has no `alert` kind. DEV-WATCH needs notify/1 kind alert, so the first registry change adds
`alert`.

**Channels and allowed forms:**

| channel | direction | forms | checker |
|---|---|---|---|
| boundary | cloud → VM | spec/1, ask/1 (and batch/1 Ops→Dev, verify/1, incident/1 Ops→Dev when addressed to VM roles) | boundary adapter |
| boundary | VM → cloud | status/1, opinion/1, incident/1, shadow/1, notify/1 (ack: SHA report, alert) | boundary adapter |
| Dev-VM ↔ Ops-VM | internal | release/1, verify/1, incident/1 (same meanings as flow.py) | ga.forms |
| Ops core ↔ worker | internal | work/1 (ga/net/pool.py item_problems :186), directive/2, report/2, verdict/1 | ga.forms |
| journal | internal | journal/1 (new: `{id, at, item, from_state, to_state, event, guard, inputs_hash, record}`) | ga.forms |
| gateway | internal | card/1 (role + evidence, fixed max), answer/1 (one allowed token + reasons) | gateway |

**Boundary rules** (rev2, kept):
- Fields are `id`, `from`, `to`, `at`, `ref`, and the form name with `/n`.
- A duplicate `id` is answered once. An unknown form or field is rejected, and the rejection is journaled and
  reported in the hourly status/1.
- The cloud never reads VM repos or logs.

**Transport (decision D1).** The boundary adapter is the only VM component that touches the baseline clone, and only
`ops/flow/inbox/{vm-dev,vm-ops}` (read) and the outbox it sends through.
- It copies admitted messages into the role repo's `inbox/` (§10).
- The Dev and Ops baselines never read the baseline repo. Their runtime dependency is the channel, not baseline code.
- Adding the `vm-dev` and `vm-ops` roles to flow.py EDGES is a registry change in VI-06 and stays shadow until cutover.

## 2. Work-item state machine

States: PLANNED → DISPATCHED → ACTING → REPORTED → VERDICT → (SEND_BACK | INTEGRATED) → DEPLOYED → OBSERVED.
Side states (decision D2): SHADOW (a criterion that cannot be executed), BLOCKED (waiting for a ladder step or the
user), CANCELLED (halt, or the spec is withdrawn).
- A state is fold(journal). Every transition appends one journal/1 row before anything else happens.
- Replaying the same events gives the same states.
- A work item is a work/1 with `{id, role, goal, files, after, done_when, check}` (pool.py :186).

Deadlines are policy keys `vm_policy.deadlines.<key>`. Only the user sets them (§13 Q2). Every deadline arms the
single deadline timer (§7).

| # | transition | trigger (event) | guard (deterministic) | actor | record written | deadline key | failure path |
|---|---|---|---|---|---|---|---|
| T1 | ∅ → PLANNED | spec/1 or batch/1 admitted at boundary | form valid; id unseen; planner rule maps the spec to work/1 items with `item_problems == []`, no `after` cycle (pool `_cycle` :229), `files` set | Planner (Ops core) | journal planned + work/1 per item; status/1 `planned` | `plan_s` | rule cannot split → needs_judgment → ladder §6; ladder exhausted → BLOCKED + status/1 blocker |
| T2 | PLANNED → DISPATCHED | scheduler pass (§5) | every `after` item INTEGRATED; `files` disjoint from all items in DISPATCHED..VERDICT (`pool.overlap` :175 false); concurrency < `vm_policy.sessions.max_concurrent`; no live session for this item; item estimate ≤ `build_per_item_usd.default`; mode allows its class (§5) | Scheduler → Session manager (admission) | journal dispatched + directive/2 id + base sha | none (waits in PLANNED) | refused → shadow/1 `rejected_by: policy|budget`, item stays PLANNED |
| T3 | DISPATCHED → ACTING | worker start event (session unit active, worktree at base sha) | session admitted; worktree head == recorded base sha | Session manager | journal acting {session, base} | `dispatch_ack_s` | no start → session `ended(error)`; back to PLANNED once (`retries.dispatch`), then BLOCKED |
| T4 | ACTING → REPORTED | worker report/2 naming a commit sha | report/2 valid; commit gate pass for that sha (VMHUB §1.3) | Worker → Commit gate | journal reported + commit-gate decision {sha, rule ids, evidence} | `vm_policy.sessions.timeout_s` | gate fail → one evidence card to the same session (budgeted) then FAILED → BLOCKED; timeout / budget_stop (net/checkpoint.py `budget_stop` :31 = checkpoint) → PLANNED with checkpoint, spend counts once to the item |
| T5 | REPORTED → VERDICT | report recorded (event) | refenv ready; head == sha; inputs hash recorded | Verdict (`ga verdict`, R2/R3-DET, 0 model) | journal verdict-start {inputs_hash} | `verdict_s` | refenv/infra error → retry once, then incident/1 (kind environment), BLOCKED |
| T6 | VERDICT → SEND_BACK | decision SEND_BACK(reason) | survived mutation, ancestry broken, file outside `files`, test not red on base, or revert does not fail the test; `sendbacks < sendback_cap` (hub.py SENDBACK_CAP, made a policy key) | Verdict | verdict/1 + templated send-back card (file, line, expected), 0 model (GA_ENGINE_OPS O4/O7) | - | cap reached → BLOCKED → ladder |
| T6' | SEND_BACK → DISPATCHED | send-back recorded | same guards as T2 (files and lock still held) | Scheduler | journal | - | as T2 |
| T7 | VERDICT → SHADOW | a criterion cannot be executed | criteria not executable (DEV-R3-DET line 4) | Verdict | verdict/1 class insufficient; status/1 to cloud | - | terminal until a new spec; never integrated |
| T8 | VERDICT → INTEGRATED | decision ACCEPT | item is next in integration order (§3.4); re-check of ancestry against the current integration head; push gate pass (VMHUB §1.4: ref in `push_allowed`, ff or clean merge, no force, revert proven); halt off | Ops core (only push credential) | push row {sha, ref, actor, gate evidence}; status/1 {sha, ref} | `integrate_s` | head moved, not ff and not a clean merge → SEND_BACK "re-merge <head>"; push gate fail → BLOCKED + status/1 failed check; nothing outside changes |
| T9 | INTEGRATED → DEPLOYED | ga-update installs a SHA that contains the integrated sha (§9) | running SHA (DEV-VMSHA report) is a descendant of the item sha | ga-update / Ops worker | journal deployed {running_sha} | `deploy_s` (Ops uses 2 h today, OPS_VMHUB.md) | deadline passed → incident/1 deploy_mismatch |
| T10 | DEPLOYED → OBSERVED | observation window ended | no alarm in the window that the attribution rule (§4.2) maps to this sha | Ops worker | journal observed; DORA row | `observe_window_s` | alarm attributed → incident/1; a stabilize item (revert or fix) is PLANNED with priority; change-failure counted |
| T11 | any → CANCELLED | `halt: true`, kill switch, or spec withdrawn by the cloud | halt read every step | Ops core | journal cancelled; sessions ended | - | worktrees kept for evidence |

**Pre-cutover (shadow) meaning:**
- T8 pushes only to `vm-shadow/<branch>`.
- The authoritative integration stays with the cloud integrator.
- T9/T10 track the **cloud-integrated** sha the VM receives through ga-update, not the VM's own shadow ref.
- Each VM verdict is scored against the cloud verdict (agree/disagree) in the hourly report.

## 3. Dev worker (code; replaces the Dev hub's routine work)

### 3.1 Parallel dispatch
- The input is the set of PLANNED items in priority order (§5).
- Each pass is greedy and deterministic. Walk the items in order and pick an item if (a) all `after` items are
  INTEGRATED, (b) `files` does not overlap any running or already picked item (`pool.overlap`), and (c) its admission
  passes.
- Stop at `max_concurrent`. The picked set is conflict-free by construction.
- Ties break by item id, so the same journal gives the same set.
- File ownership is held from DISPATCHED until INTEGRATED, SHADOW or CANCELLED. Hub `owned` globs (hub.py `_one`
  :1765) become this lock.

### 3.2 Act loop (inside a worker session)
- The executor is `ga act` (act/loop.py `Act`, `run_item` :572). It picks a rung with `act/route.py` (LADDER :29,
  `plan_rungs` :87) and builds a card with `act/card.py` (CARD_MAX 2048 B).
- Every model call goes through the gateway (call sites loop.py :626/:674 are rewired in VI-03).
- The worker edits, tests and commits in its own worktree. A PRE_PUSH hook rejects every push, and the worker has no
  push credential (VMHUB §1.2).
- Done when `done_when` passes locally, then report/2 with the commit sha.

### 3.3 Verdict (DEV-R3-DET)
- `ga verdict` is a pure function of executable checks, with 0 model calls:
  - head == sha, ancestry, allowed files;
  - acceptance test identical to the spec's and red on base;
  - full suite green in the refenv;
  - diff mutations (`verify/mutate.py mutations` :399, generated by code) all killed or cross-covered;
  - revert makes the test fail.
- Building blocks: `judge.judge()` :365 and `judge_commit` :435.
- It replaces `MailHub._decide` hub.py:1844 (model turn at :1856). The deterministic overrides at :1771-1783 become
  the whole decision.
- A test fails if the verdict or integration modules import the gateway.

### 3.4 Integration order
- Topological order on `after`, then batch/1 `order` index, then ACCEPT time, then id.
- Only the head of that order may integrate. Each integration re-checks ancestry against the current integration head
  (T8), so a later item is never integrated over an unverified base.

### 3.5 Versioning and SHA reporting (DEV-VMSHA)
Decision D3:
- Every integration, deploy and measurement is identified by **full SHA**.
- The version number is a release label that Dev assigns in release/1 in landing order. It is not bumped per item.
- ga-update (core.py `_notice` :709 sends one message per *version* today) is changed to send one notify/1 per
  **SHA change**, and to answer an `ask/1 {question: "sha"}` within one update cycle.
- The hourly report carries the running SHA and the policy hash. Ledger rows carry the SHA (R1R2 A').

## 4. Ops worker (code; GA57 `ga ops tick` per GA_ENGINE_OPS §3)

### 4.1 Observe (0 model calls)
Sources are local only. The cloud is never read beyond the published snapshot:
- journal;
- gateway ledger `~/.ga/llm/ledger`;
- hub/act ledgers;
- refenv test results;
- systemd unit state (console `services.py`);
- `ops/hub/cloud_sessions.json` snapshot (DEV-WATCH; the baseline clone is read only through the boundary adapter's
  fetch).

### 4.2 Rules
- A `rule/1` table maps condition → anomaly kind + evidence.
- First rules: O1 cap_reached, O2 decide_no_model, O4 mut_survived, O7 base_drift (GA_ENGINE_OPS §2), plus
  deadline_missed (any T-deadline) and the watcher rules (§4.3).
- Every action has an `action-spec/1 {name, risk, preconditions, postcondition, window_ms}`.
- Existing deterministic rules keep running inside the gates: `rules.py` R1-R13 (r2_ownership :75, r3_push :89,
  r6_secrets :138, r12_budget :212), and gates.py Gate 1-7 to classify user questions.
- Attribution rule (T10): an alarm is attributed to the latest DEPLOYED sha whose diff touches a file in the alarm's
  evidence. Otherwise it is unattributed and still counts toward the SLO. (Decision D4.)

### 4.3 Guard / VERIFY / alerts
- Guard uses rlo risk classes:
  - low: execute (retry_next_rung, rerun_on_base, send_back_template);
  - medium: execute and report;
  - high (push, credential, cost, policy): never executed by code; status/1 blocker to the user via baseline.
- VERIFY checks the postcondition inside `window_ms`. A failure re-enters one ladder step up. The same failure twice
  is BLOCKED and reported, with no endless retry.
- **Watcher (DEV-WATCH)** fixed rules: ctx > `ctx_cap_tokens` on a non-completed session, session USD/h >
  `session_usd_per_h`, total USD/h > `total_usd_per_h`, snapshot age > `snapshot_max_age_h`.
  - Thresholds are read from `watch_thresholds.json` (Ops-owned) on every evaluation, so a commit to the file takes
    effect without a code change.
  - Alarms go out as notify/1 kind alert to baseline-ops, once per kind per session per UTC day (dedup key in the
    journal). A stale snapshot alarm also reaches the user.
  - No model on this path (test).

### 4.4 SLO and DORA (computed by code from the journal; Ops proposed `ops/hub/dora.py`)

| metric | definition | source |
|---|---|---|
| deployment frequency | DEPLOYED transitions per day (KST day) | journal T9 rows; pre-cutover, cloud ACCEPT rows in `baseline_verdicts.jsonl` + VMSHA reports |
| lead time for changes | t(INTEGRATED) − t(DISPATCHED), median and p90 (GA_ENGINE_OPS §6); deploy lag t(DEPLOYED) − t(INTEGRATED) also kept | journal |
| change failure rate | items with an attributed alarm in the T10 window / DEPLOYED (D5). Kept separately: send-back rate = SEND_BACK / verdicts (GA_ENGINE_OPS §6 definition) | journal |
| time to restore | alarm raised → rule condition false again (alarm cleared) | journal alert rows |
| verdict latency | t(VERDICT end) − t(REPORTED) | journal |
| spend | USD per cap window, per item, 0-call share | gateway ledger |

Each SLO lives in `slo.json` as `{name, metric, objective (threshold), target (fraction good), window}`. GA_ENGINE_OPS
§6 gives example objectives (verdict < 30 min, lead time < 2 h, change failure < 20 %). They are **not adopted**
until the owner sets them (§13 Q4).

## 5. DevOps scheduler

**Error-budget rule (precise).**
- For each SLO *s* over its rolling window *W_s*:
  - `budget_s = (1 − target_s) × events_s(W_s)`
  - `bad_s` = events in *W_s* that violate the objective
  - `remaining_s = 1 − bad_s / budget_s` (with `budget_s = 0` → remaining = 1 if `bad_s = 0`, else −∞)
- `mode = STABILIZE` if any `remaining_s ≤ 0`, or if an open incident/1 of a kind listed in
  `vm_policy.scheduler.stabilize_kinds` exists. Otherwise `mode = DEV`.
- Hysteresis (D6): STABILIZE switches back to DEV only when every `remaining_s ≥ vm_policy.scheduler.resume_fraction`.
- Fewer than `vm_policy.scheduler.min_events` events in a window → that SLO is ignored (no flapping on tiny samples).

**Mode effect.**
- STABILIZE dispatches only items of class `stabilize` (revert, fix, rule, flaky-test). Feature items stay PLANNED;
  they are never cancelled.
- DEV dispatches all classes. Stabilize items still sort first.

**Priority key (total order).**
1. class rank: stabilize first;
2. spec stage (R0 < R1 < … R5);
3. batch/1 `order` index;
4. PLANNED time;
5. id.

**Concurrency and budget.**
- `n = min(vm_policy.sessions.max_concurrent, |conflict-free set|)`.
- Per-item and global spend are refused by the gateway caps (`vm_budget.caps.*`). The scheduler does not dispatch an
  item whose estimate is above `build_per_item_usd.default` without a ladder step (soft cap). `hard` is never passed.
- If a cap window is exhausted, the scheduler dispatches nothing that needs a model until the window frees. Pure-code
  items (verdict, rules) continue.
- Every scheduler decision is journaled with its inputs, so it replays.

## 6. Escalation ladder (judgments, not build work)

Order: rule → cheap model → strong model → model session → user. Policy keys are under `vm_policy.ladder`. Values are
the user's (§13 Q3).

| step | taken when | budget per step | output accepted when |
|---|---|---|---|
| 0 rule | always first | 0 USD | rule returns a decision. If no rule matches, or a rule says it cannot decide, the result is `needs_judgment{reason, evidence}` |
| cache | needs_judgment and the fingerprint (purpose + normalized evidence + ga-sdk SHA + served model + policy hash; R1R2 A') was seen | 0 | cached answer passes the same validation as a fresh one |
| 1 cheap | needs_judgment, purpose ∉ `ladder.strong_only_purposes` (default from `vm_budget.model`: opinion, diagnosis) | ≤ `ladder.cheap_max_calls` calls, card ≤ `ladder.card_max_bytes`, ≤ `ladder.cheap_max_usd` | answer ∈ the allowed answer set of the purpose; preconditions of the named action-spec hold; `confidence ≥ ladder.cheap_min_confidence`; for risk ≥ medium, `ladder.agree_n` independent samples agree |
| 2 strong | cheap answer invalid, below confidence or disagreeing; or purpose ∈ strong_only | ≤ `ladder.strong_max_calls`, ≤ `ladder.strong_max_usd` | same validation |
| 3 model session | strong answer still invalid, or the judgment needs multi-step tool use (a hard task, GA_ENGINE_RUNTIME §4D). **Pre-cutover:** this step is a status/1 `needs` to the cloud Dev hub (VM sessions are HELD) | ≤ `build_per_item_usd.default` (soft) / `.hard` | session output is a proposal: it re-enters at step 0 as new evidence |
| 4 user | same failure twice at step 3; Guard risk high; Gate 1-7 class (gates.py: budget/credential G6, new repo/session G7, policy, cutover); a cap refusal that persists past `ladder.refusal_wait_windows` windows; any cloud-platform denial | 0 VM spend | status/1 blocker (via baseline, morning list if overnight) |

**Notes:**
- Every model answer is a proposal. The deterministic validator decides, and an invalid answer is never executed.
- Gateway refusal at any step → shadow/1 `rejected_by: budget`. The item goes to BLOCKED, never to the next step
  (a refusal is not a reason to escalate to a costlier model).
- **Judgment → rule** (DEV-VMAUTO line 3; decision D7):
  - The R1 cache already gives 0 calls on an exact fingerprint repeat.
  - After `ladder.promote_after` identical validated answers on the same fingerprint, minus SHA and served model, the
    Ops core writes a learned rule `{fingerprint, purpose, answer, n, first_at, last_at, models}` to
    `rules/learned.jsonl` in the role repo, through the commit gate.
  - A learned rule is invalidated by a policy hash change, or by Ops disabling it (a data change).
  - Learned rules count in the hourly 0-call share.

## 7. Event-driven wakeups with explicit deadlines

One processing entry point: `ga devops step`.
- It drains `~/.ga/vm/events/` in name order, applies every due deadline, then re-arms the deadline timer.
- It is idempotent: an event file is removed only after its journal row is written.

| event source | how it arrives | emits |
|---|---|---|
| boundary message | `ga-fetch.timer` fetches the channel; the adapter writes admitted files | `inbox.<id>` → T1 / ask |
| worker started / exited | systemd unit of the session, ExecStartPost / ExecStopPost writes an event | T3 / T4 timeout path |
| worker commit | post-commit hook in the worktree writes an event | commit gate run |
| report/2 | worker outbox file | T4 |
| verdict done / push done | written by `ga verdict` / Ops core | T6/T7/T8 |
| new SHA installed | ga-update after ff + reinstall | T9, VMSHA notify/1 |
| watcher snapshot changed | fetch sees a new `cloud_sessions.json` hash | §4.3 rules |
| policy changed | inotify on `/etc/ga/vm_policy.json` (`ga-policy.path`) | reload + halt check |

Named timers (the only time-based wakeups; their intervals are policy keys unless marked existing):

| timer | interval | purpose | replaces |
|---|---|---|---|
| `ga-devops.path` | event (PathChanged on events dir) | runs `ga devops step` | `ga-hub.timer` 60 s polling (core.py :150-152) |
| `ga-deadline.timer` | one-shot, `OnCalendar` = earliest open deadline in journal | deadline transitions | - |
| `ga-fetch.timer` | `vm_policy.boundary.fetch_s` | git fetch of the boundary channel (git has no push notification to the VM) | `ga hub tick` mailbox fetch |
| `ga-update.timer` | 30 min (existing, core.py :162) | ff-only update + SHA report | kept |
| `ga-report.timer` | hourly (spec: hourly boundary report) | status/1 report, policy hash | - |

No other loop sleeps or polls. Workers block on their own process; nothing waits in a `while True`.

## 8. Ops core (already designed: `research/VMHUB_DESIGN.md` r2, approved with Ops' points taken in)

| part | one-line summary | VMHUB_DESIGN |
|---|---|---|
| Gateway | `ga.llm.call(card, purpose, item_id)`: the only model path. Every cap checked before the call, actual USD reconciled after, ledger row per call, rule cache, single-site test | §1.1; R1R2 A |
| Session manager | `requested → admitted|refused → running → ended(reason)`; caps from `vm_policy.sessions`; one session per item; refusal → shadow/1 | §1.2 |
| Commit gate | tests, allowed paths, branch, diff size, secrets, 0 model; decision + evidence per commit | §1.3 |
| Push gate | `push_allowed` ref (shadow refs until cutover), verdict ACCEPT, mutations, revert proven, ff/merge, no force; only the Ops core holds the credential; status/1 {sha, ref} per push | §1.4 |
| Policy | enforcing root-owned `/etc/ga/vm_policy.json`, baseline mirror hash-compared hourly by Ops; missing = halt | §2 |
| Kill switch | 3 layers outside the VM: soft `halt: true`; provider spend limit / key revoke; instance stop / push-credential revoke | §3 |
| Boundary + journal | registry forms, dedup by id, append-only journal, replay, idempotent outbox | §1.5 |

This doc adds only the wiring: the state machine (§2) calls the session manager at T2/T3, the commit gate at T4 and
the push gate at T8. The scheduler (§5) and the ladder (§6) read their keys from the same enforcing policy.

## 9. Today's VM services → design

| today (ga/vm/core.py @277945d) | fate | when (build item) |
|---|---|---|
| `ga-console.service` (`ga console`, :147) | **kept**; gains a read-only view of journal/state snapshot and ledger | VI-12 (adds DORA panel) |
| `ga-hub.timer` 60 s + `ga hub tick --shadow` (:150-152; hub_conf `backend agv`, `daily_turns 40` :175; model turn hub.py:1856) | **replaced** in two steps: (1) the decision becomes `ga verdict` (0 model) in VI-04/VI-04b, so the shadow hub stops spending model turns; (2) the tick is replaced by `ga-devops.path` + state machine | (1) VI-04b; (2) VI-14, after a 24 h side-by-side agreement check by Ops; then **retired** with `~/.ga/hub.json` and hub ledger (superseded by the gateway ledger) |
| `ga-update.timer` 30 min, ff-only, `_notice` per version (:162, :709) | **kept**; `_notice` becomes per SHA plus a SHA answer to ask/1 (DEV-VMSHA); later emits the T9 event | VI-01; VI-14 |
| agy bridge unit (runs `~/baseline/ops/agy_bridge/bridge.py`, :203-212) | **replaced** by the `ga bridge` unit (ga/bridge, same config keys), which removes the runtime dependency on the baseline repo. **Retired** when worker sessions run under the session manager; agy then remains only as a gateway backend | VI-20 (not held); retire at VI-15 (HELD) |
| `ga act` / agv (act/loop.py, ask/solve.py) | **kept** as the worker executor; model calls rewired through the gateway | VI-03 |
| `ga bridge` tools (ga/bridge/tools.py) | **kept** (worker tool table) | - |
| cloud Claude token-watcher session | **retired** by DEV-WATCH after Ops' 24 h side-by-side | VI-05 |
| cloud integrator session | stays the **authority** until cutover; then replaced by T8 VM push | cutover spec (user) |

## 10. Repository layout: cogito5170/Dev and cogito5170/Ops (VMHUB rev2; build HELD, VI-18)

Each repo holds everything its baseline needs on the VM. The code comes from the installed ga-sdk package (pinned by
SHA). Neither repo reads the baseline repo at runtime (§1 D1). The cloud never reads either repo.

```
cogito5170/Dev                         cogito5170/Ops
├── README.md      role pointer        ├── README.md
├── ga.lock        ga-sdk SHA + pins   ├── ga.lock
│                  hash                │
├── role/                              ├── role/
│   └── DEV_BASELINE.md (transplanted  │   └── OPS_BASELINE.md
│       from baseline ops/hub/roles,   │
│       then owned here)               │
├── rules/                             ├── rules/
│   ├── planner.json  spec→work/1      │   ├── ops_rules.json   rule/1 (O1..O10)
│   │                 rules            │   ├── actions.json     action-spec/1
│   ├── verdict.json  sendback         │   ├── learned.jsonl
│   │                 templates        │   └── scheduler.json   class map for §5
│   └── learned.jsonl promoted         │
│       judgments (§6)                 │
├── notes/                             ├── limits/
│   ├── NOTES.md   working notes       │   ├── watch_thresholds.json  (Ops-owned
│   │              (fixed size)        │   │                           values)
│   └── decisions.jsonl                │   └── slo.json               (§4.4)
├── inbox/   <ts>-<from>-<form>-       ├── notes/  NOTES.md, decisions.jsonl
│            <id>.json (written only   ├── inbox/  outbox/
│            by the boundary adapter)  │
├── outbox/  pending sends, idempotent ├── policy/ mirror.json + mirror.sha256
│            by id                     │
├── policy/                            ├── registry/ forms.sha256
│   ├── mirror.json   read-only mirror │
│   │                 of vm_policy     │
│   └── mirror.sha256 enforcement uses │
│                     /etc/ga/...      │
├── registry/                          ├── measure/ hourly.jsonl, dora.jsonl,
│   └── forms.sha256  pin of ga-sdk    │            r0_runs.jsonl (VMSHA R0 set)
│                     registry         │
├── work/                              ├── incidents/ <id>.json
│   ├── items/<id>.json   work/1       │
│   └── verdicts/<id>.jsonl verdict/1  │
│       inputs + outputs               │
└── state/                             └── state/  journal/, snapshot.json
    ├── journal/<date>.jsonl journal/1
    └── snapshot.json        fold(journal)
```

**Write rules:**
- `inbox/` is written only by the boundary adapter.
- `state/` is written only by the Ops core: the live journal is on disk at `~/.ga/vm/<role>/` and is committed to
  the repo at each hourly report through the commit gate (D8).
- `policy/` is written only from a verified mirror copy; a mismatch with `/etc/ga` raises an incident.
- `limits/` in the Ops repo is changed only by Ops commits.
- Pushes go to the repo's VM-owned branch only, through the push gate.

**Transplant:** role files and notes are copied once from baseline `ops/hub/roles/*` at VI-18. After that the baseline
keeps only the cloud-side top role.

## 11. Acceptance map

**DEV-VMHUB rev2 (still holds per rev3 line 1)**

| line (short) | part |
|---|---|
| "Dev and Ops each hold everything their baseline needs…; neither depends on baseline ops/flow at runtime" | §10, §1 D1 |
| "boundary admits only cloud→VM spec/ask, VM→cloud status/opinion/incident/shadow; other rejected + recorded" | §1 channel table, boundary rules; VMHUB §1.5. notify/1 ack/alert are added by a registry change (§13 Q7) |
| "existing fields only; id identity, ref answers; duplicate id answered once" | §1 |
| "cloud operates without reading VM repos/state/logs" | §1, §10 |
| "authority, routing, transitions, admission, integration deterministic; replay same" | §2 (journal fold), §3.1, §3.4, §5 |
| "VM internals updated by pipeline; boundary change = new /n" | §9 ga-update, §1 registry |
| "restart resumes, no lost/duplicated message" | §7 idempotent step; VMHUB §1.5, §3 |

**DEV-VMHUB rev3**

| line (short) | part |
|---|---|
| "everything in rev2 still holds" | table above |
| "worker can commit, any push fails; only Ops core pushes after commit + push gate" | §3.2, §2 T4/T8, VMHUB §1.2-§1.4 |
| "commit gate from tests/paths/branch/diff/policy, 0 model, recorded per commit" | §2 T4, VMHUB §1.3 |
| "push gate separate, higher; status/1 per push naming sha and ref" | §2 T8, VMHUB §1.4 |
| "Ops core creates/ends sessions within caps…; over cap → shadow/1" | §2 T2/T3, §5, VMHUB §1.2 |
| "every VM model call through the single gateway" | §3.2, §6, §8, VMHUB §1.1 |

**DEV-VMAUTO**

| line (short) | part |
|---|---|
| "VM runs intake→batch→build→verify→integrate→observe as code, directed by cloud via flow forms" | §2 T1-T10, §3, §4, §7 |
| "one gateway records served/tokens/USD, refuses over budget (shadow/1), test no other site" | §8, R1R2 A1-A6 |
| "model only on needs_judgment; verdict/integration no model; repeated judgment → rule, 0 calls" | §6 (cache + learned rules), §3.3 |
| "fixed-size card, never history; context size recorded" | §1 card/1, §6 `ladder.card_max_bytes`, R1R2 A1/A3 |
| "Dev states per remaining call site why rules cannot decide" | §12 VI-03 deliverable: a call-site table (site, purpose, ladder step, why no rule) |

**DEV-VMBUDGET**

| line (short) | part |
|---|---|
| "every call checked against all vm_budget caps; over → refused, shadow/1" | §8 gateway, §6 notes, R1R2 A2 |
| "a test shows each cap refusing at its limit" | R1R2 A7 (VI-02) |
| "VMHUB rev3 design doc exists: components, states, policy fields, failure/rollback, acceptance map" | VMHUB_DESIGN r2 §1-§4; this doc §0, §2 |
| "Ops gives opinion/1 before any build request" | §14 review status |

**DEV-R3-DET**

| line (short) | part |
|---|---|
| "integrate decision pure function of executable checks (head==sha, ancestry, files, test red on base, suite green, mutations killed, revert fails)" | §3.3, §2 T5-T8 |
| "mutations from the diff by code" | §3.3 (`verify/mutate.py`) |
| "no model call on verdict/integration path; test fails if added" | §3.3 import test |
| "non-executable criteria never integrate: shadow + reported" | §2 T7 |
| "VM pushes itself under a once-approved policy; ff/merge to the one integration ref, never force" | §2 T8, VMHUB §1.4. **HELD**: pre-cutover the target is shadow refs only; the integration ref needs cutover (§13 Q1) |
| "same input → same verdict, replayable" | §3.3, R1R2 B3 |

**DEV-VMDESIGN (this spec)**

| line (short) | part |
|---|---|
| "one doc covers every planned VM part …" | §1-§8 |
| "today's VM services: kept/replaced/retired, when" | §9 |
| "layout of cogito5170/Dev and /Ops" | §10 |
| "maps VMHUB rev3, VMAUTO, VMBUDGET, R3-DET; build order in one-worker items" | §11, §12 |
| "Ops opinion/1; baseline approves (overnight_delegation); one finished doc in the morning" | §14 |

## 12. Build order (one worker each; base = R0-baseline)

| id | scope | spec | depends on | held? |
|---|---|---|---|---|
| VI-01 | ga-update `_notice` per SHA; ask/1 "sha" answer; R0 test set run with result in a repo Ops reads; test: same-version SHA change → exactly 1 report | DEV-VMSHA | - | not held |
| VI-02 | `ga/llm` gateway core: caps, applies/windows from policy, reconciliation, ledger, halt, per-cap tests | VMAUTO, VMBUDGET | - | not held (built tonight, R1R2 A) |
| VI-03 | rewire every model call site to the gateway + single-site test + per-site "why no rule" table | VMAUTO | VI-02 | not held |
| VI-04 | `ga verdict --dry-run` + replay over `baseline_verdicts.jsonl` | R3-DET (R2) | - | not held (R1R2 B) |
| VI-04b | shadow hub decision = `ga verdict` (remove model turn hub.py:1856); test: no gateway import on the verdict path | R3-DET | VI-04, VI-03 | not held |
| VI-05 | watcher: snapshot + ledgers, 4 rules, thresholds file, dedup, notify/1 alert; 0-model test | DEV-WATCH, OPS-LIMITS-WATCH | VI-06a | not held |
| VI-06a | registry: add notify/1 kind `alert` (minimal registry change) | FORMATS | - | not held |
| VI-06 | single registry file; flow.py + ga.forms read it; disagreement test; docs generated; reject + record unknown | DEV-FORMATS | VI-06a | not held |
| VI-07 | hourly gateway summary (`ga llm report --hour`) as status/1-ready JSON | VMBUDGET (Ops point) | VI-02 | not held |
| VI-08 | ladder: needs_judgment result type, cheap→strong steps, `vm_policy.ladder` keys, validator; refusal ≠ escalation test | VMAUTO | VI-03 | not held; values = user (§13 Q3) |
| VI-09 | learned rules: promotion after `promote_after`, invalidation by policy hash, 0-call share | VMAUTO | VI-08 | not held |
| VI-10 | journal/1 + state fold + replay test (state machine T1-T11 in shadow, no sessions: T2-T4 recorded as `would_do`) | VMAUTO | VI-06 | not held |
| VI-11 | Ops worker `ga ops tick`: rule/1, action-spec/1, Guard, VERIFY, alert (O1, O2, O4, O7) | VMAUTO (GA57) | VI-10, VI-05 | not held |
| VI-12 | SLO/DORA computation from the journal + console panel | VMAUTO observe | VI-10 | not held; `slo.json` values = owner (§13 Q4) |
| VI-13 | scheduler: priority key, conflict-free set, error-budget mode with hysteresis (decisions journaled, shadow) | VMAUTO | VI-10, VI-12 | not held |
| VI-14 | event wakeups: `ga-devops.path`, `ga-deadline.timer`, `ga-fetch.timer`, `ga-report.timer`; retire `ga-hub.timer` after Ops' 24 h side-by-side | VMAUTO | VI-10, VI-01 | not held; deadline values = user (§13 Q2) |
| VI-20 | `ga bridge` unit replaces `baseline/ops/agy_bridge/bridge.py` unit | VMHUB rev2 (no runtime baseline dep) | - | not held |
| VI-15 | session manager (admission caps, worktree, PRE_PUSH, no credential, end reasons) | VMHUB rev3 | VI-02, VI-10 | **HELD** |
| VI-16 | commit gate | VMHUB rev3 | VI-15 | **HELD** |
| VI-17 | push gate + VM push credential limited to shadow refs | VMHUB rev3, R3-DET push | VI-16, VI-04b | **HELD** |
| VI-18 | cogito5170/Dev + /Ops skeleton per §10, transplant role/notes, boundary adapter (inbox copy, dedup, outbox idempotent) | VMHUB rev2 | VI-06, VI-10 | **HELD** (+ user creates repos, Gate 7) |
| VI-19 | kill-switch layer 1 test + push-credential revoke drill (Ops records time-to-stop) | VMHUB rev3 | VI-17 | **HELD** |
| VI-21 | cutover (VM becomes authority, cloud hubs read-only archive) | separate spec | all | user only |

Parallel groups (no shared files): {VI-01, VI-02, VI-04, VI-06a, VI-20} → {VI-03, VI-05, VI-06, VI-07} →
{VI-04b, VI-08, VI-10} → {VI-09, VI-11, VI-12} → {VI-13, VI-14}. VI-15..VI-19 wait for the user's release of the
VMHUB hold.

## 13. Open questions (user only; not guessed)

| # | question | why it is the user's |
|---|---|---|
| Q1 | When does cutover happen, and is the VM integration ref the existing `claude/gracious-meitner-vp49xe` or a new one? | never two primaries; push authority |
| Q2 | `vm_policy.deadlines.*` values: plan_s, dispatch_ack_s, verdict_s, integrate_s, deploy_s (Ops uses 2 h today), observe_window_s; `boundary.fetch_s` | user-owned VM policy Ops default proposal: plan_s 900, dispatch_ack_s 600, verdict_s 1800, integrate_s 1800, deploy_s 7200, observe_window_s 3600, boundary.fetch_s 300 |
| Q3 | `vm_policy.ladder.*` values: cheap/strong max calls and USD, cheap_min_confidence, agree_n, promote_after, refusal_wait_windows, card_max_bytes; `strong_only_purposes` | spend and autonomy level |
| Q4 | SLO set and targets, and who owns `slo.json` (Ops as operating limits, or the user); `scheduler.resume_fraction`, `min_events`, `stabilize_kinds` | decides when feature work stops Ops proposal: Ops owns slo.json as operating limits (initial values shown to the user once, changes announced in status/1): verdict latency p90 < 30 min target 0.9/24 h; lead time median < 2 h target 0.8/7 d; change failure < 20 %/7 d; time to restore < 1 h target 0.9/7 d; min_events 5; resume_fraction 0.5; stabilize_kinds [deploy_mismatch, boundary_violation, budget_overrun, two_primaries] |
| Q5 | `vm_policy.sessions{max_concurrent, max_children, timeout_s, per_day_usd}` and `push_allowed` shadow refs | already on the morning list (ASK-VMHUB-DESIGN-APPROVAL) |
| Q6 | Create cogito5170/Dev and cogito5170/Ops (Gate 7 new repo) and give the VM a push credential limited to their VM branches and shadow refs | credential / new repo |
| Q7 | RESOLVED by Dev+Ops (forms are a Dev+Ops contract, OP-OPS-VMINT): the boundary carries notify/1 VM->cloud with exactly two registered kinds, ack (SHA report / sha answer) and alert; status/1 stays the hourly summary. Recorded in the registry change VI-06a/VI-06. Not a user question. | — |
| Q8 | Day window rolling 24 h vs KST calendar day (`vm_budget.windows.day`) | already open from R1R2 |
| Q9 | Model credential on the VM, provider spend limit, writing `/etc/ga/vm_policy.json` over SSH, instance-stop path | credentials / kill switch layers 2-3 |

## 14. Review status
- Ops: opinion/1 requested on this doc before any VMHUB build request (DEV-VMDESIGN line 5, DEV-VMBUDGET line 4).
- Baseline may approve on the user's behalf under `overnight_delegation` (until 2026-10-07 09:00 KST) once Ops'
  points are taken in. The VMHUB build stays HELD regardless.
- Decisions made here that were not dictated by inputs: D1 (boundary adapter is the only reader of the baseline
  clone), D2 (side states), D3 (SHA identity, version per release), D4 (alarm attribution), D5 (change-failure
  definition), D6 (hysteresis), D7 (learned-rule promotion), D8 (journal committed hourly). Each is open to Ops'
  opinion.

## 15. Revisions r2 (Ops OP-OPS-VMINT taken in full; nothing rejected)
- D4 attribution (§4.4): an alarm is attributed to EVERY DEPLOYED sha within observe_window_s whose diff touches a
  file in the alarm's evidence (CFR counts each item at most once). Alarms of kind environment/infra/budget never
  count toward CFR but do count toward their SLO. A revert or fix item later PLANNED for a sha marks that sha failed
  even without file evidence.
- D6 scheduler (§5): new key `vm_policy.scheduler.max_stabilize_s`; on expiry status/1 blocker to the cloud (user
  decides); feature items are still never cancelled. Missing data never counts as good: an SLO whose data gap exceeds
  window/4 is reported `unknown`, not remaining=1, and `unknown` does not release STABILIZE.
- §0 thresholds: until VI-18 (Ops repo, held) the boundary adapter copies ops/hub/watch_thresholds.json with its
  sha256 into the VM inbox; the watcher (VI-05) reads only that copy and logs the hash in every alert.
- Q7 resolved by Dev+Ops (notify/1 ack + alert across the boundary); Q2/Q4 carry Ops' default proposals for the user.
- Alert dedup: once per kind per session per KST day.
- Test (VI-05): during the 24 h side-by-side a VM alert and the cloud Ops alarm for the same condition both appear;
  Ops scores agreement; that report retires the Claude watcher.
- First builds: VI-01 (SHA reporting) + VI-06a (notify kind alert), then VI-02/VI-04/VI-20 in parallel; VI-15..19 held.
