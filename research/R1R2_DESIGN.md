# R1 gateway + budgets, R2 verdict dry-run — design (Dev, for Ops opinion and baseline approval)

Author: Dev hub session_01VMbRhMjtfPAALfLjAWJ1tT, 10-07 01:1x KST. Specs: DEV-VMAUTO, DEV-VMBUDGET (R1),
DEV-R3-DET (dry-run, R2 per DEV-OVERNIGHT). Base: ga-sdk R0-baseline = 8ead789 (integration head 318b22a).
Larger context (VM Ops core, gates; build HELD): research/VMHUB_DESIGN.md. Code refs are ga-sdk @ 318b22a.

## A. R1 — one LLM gateway with budget enforcement (DEV-VMAUTO + DEV-VMBUDGET)

Scope (what is built tonight):
1. New module `ga/llm/` (gateway): `call(card, *, purpose, item_id, model_hint=None) -> Result`.
   - purpose ∈ {coordination, intake, diagnosis, opinion, build, judge}; item_id required for build.
   - Card = role + evidence, max size from config; size recorded. No history parameter exists.
2. Budget check before every call, values read from `baseline/ops/flow/policy.json vm_budget.caps` at call time
   (path from hub.json `baseline_repo`; never constants). Windows from the gateway ledger:
   coordination/h (purpose coordination), baselines/h (coordination+intake+diagnosis+opinion), total/h,
   total/day, per item default (soft → result `needs_judgment`, no call) and hard (refuse).
   Estimate = catalog price (`backends/catalog.py`) × (card tokens + max_output). Tightest cap wins.
   After each call the actual USD (incl. cache tokens) replaces the estimate in the window (post-call reconciliation).
   Applicability purpose->caps and windows come from policy data (`vm_budget.applies`, `vm_budget.windows`; default
   until the user sets them: Ops' proposal, rolling 60 min / rolling 24 h) — not sets in code. The VM enforcing copy
   is the root-owned /etc/ga/vm_policy.json when present, else the baseline mirror (cloud/dev runs); `halt: true` or
   an unreadable policy refuses every call.
   Refusal → no call, `shadow/1 {rejected_by: "budget", reason: cap+window+estimate, would_do}` staged, result
   `refused`. Policy missing/unreadable → refuse all (fail-closed).
3. Ledger: `~/.ga/llm/ledger/<UTC date>.jsonl` one row per call: at, purpose, item_id, requested/served model,
   input/output/cache_read/cache_write tokens, usd, card_bytes, fingerprint, outcome (ok|refused|error label).
   Served-model mismatch and error labels are recorded (POLL-RUNTIME).
4. Rule cache: fingerprint = sha256(purpose + normalized evidence). A judgment returned for a fingerprint is stored;
   the same fingerprint again returns the cached answer with 0 calls (ledger row outcome `cached`).
5. Rewire every direct site to the gateway: hub.py:1662/1856, plan/cli.py:59, act/loop.py:626,674,
   net/node.py:379,469, gemini.py:246,637 (validation/probe calls marked purpose `probe`, still metered).
   Subprocess adapters (claude -p, agy, gemini CLI, agent_sdk) are invoked only through gateway-run backends.
6. Test `test_llm_single_site`: AST/grep scan of `ga/` fails on any `backends.create(`, `run_turn(`, model CLI
   subprocess or `query(` outside `ga/llm/` and `ga/backends|adapters` internals.
8. Hourly boundary report: `ga llm report --hour` writes the VMHUB_DESIGN §1.1 fields (spend vs limit per cap,
   calls, 0-call share, estimate error, refusals by cap, running ga-sdk SHA, policy sha256) as status/1-ready JSON.
7. Tests per cap: for each cap, spend just below → call allowed; estimate crossing the cap → refused, no backend
   invoked, shadow row written. Policy change (temp file) takes effect on the next call without code change.

Acceptance map: VMAUTO "one gateway records served/tokens/USD, refuses over budget, test no other site" → 1,2,3,5,6;
"model only on needs_judgment; repeat → rule, 0 calls" → 4; "fixed-size card, size recorded" → 1,3;
VMBUDGET "every call checked against all caps, shadow/1" → 2; "test per cap" → 7; "values from policy.json" → 2.
Not in tonight's scope: VM-side loop changes (VMHUB, held).

Risk: rewiring call sites touches hub/act/plan; mitigation = full suite in refenv + mutations on the cap checks.

## B. R2 — verdict dry-run without a model (DEV-R3-DET, dry-run part)

Scope:
1. `ga verdict --dry-run --branch <ref> --sha <sha> --base <ref> --spec <acceptance test path>`: runs the existing
   deterministic `judge.judge()` (fresh clone, net-blocked tests, seeded mutations), plus checks: head == sha,
   ancestry (ff or clean merge), allowed files, acceptance test identical and red on base, revert makes it fail.
   Decision = pure function of these results: ACCEPT | SEND_BACK(reason) | SHADOW(non-executable criterion).
   No push in dry-run. No model call (test fails if the module imports the gateway).
2. Replay harness: reads `baseline/ops/hub/baseline_verdicts.jsonl`, for each row with a reachable sha (ga-sdk and
   Token) recomputes the dry-run verdict and writes `{id, rev, sha, recorded, dry_run, agree, reason}` to a
   report file committed in baseline (`ops/flow/measure/R2_DRYRUN.jsonl`) + summary counts (agree / disagree /
   not reproducible).
3. Same input → same output (seeded mutation order, sorted file lists); replay twice and diff in a test.

Acceptance map: "decision pure function of executable checks" → 1; "mutations from the diff by code" → judge
seeded mutations; "no model call, test" → 1; "non-executable → shadow, reported" → 1 SHADOW; "deterministic,
replayable" → 3; "agreement count reported" (DEV-OVERNIGHT) → 2. The integrating push stays with the integrator
under policy/1 until a later spec.

## A'. Revisions r3 (Ops OP-OPS-R1R2 taken in full)
- Policy path is ONE config value (`llm.policy_path`; default baseline mirror, VM later /etc/ga/vm_policy.json) and
  the policy file sha256 is written into every ledger row; moving to the VM-local file is a config change.
- purpose->cap mapping read from policy (`vm_budget.applies`; default = the sets in A2); every purpose incl.
  probe/judge/build is under at least total/h + total/day; test that `cloud_top_baseline_usd_per_h` and
  `session_ctx_cap_tokens` are never applied by the gateway.
- Rule-cache fingerprint = sha256(purpose + normalized evidence + ga-sdk SHA + served model + policy hash).
- Estimate prices cache_read/cache_write; window uses actual USD from the ledger after each call (reconciliation).
- Day window is a policy key (`vm_budget.windows.day`; default rolling_24h, reports by KST day) — user confirms (morning).
- Soft halt: `halt: true` or unreadable policy -> every call refused; one test.
- Hourly gateway summary mailed to baseline-ops (fold over the ledger): per cap {spend, limit, refusals}, calls,
  cached share, estimate-vs-actual error, ga-sdk SHA, policy hash.
- R2 replay: unknown acceptance-test path -> not_reproducible with reason; flaky reruns counted separately.
- R1 integrate keeps 0.18.1 → land DEV-VMSHA before (or with) R1 so Ops verifies the VM by SHA; else bump version.
- Build order in A: gateway + ledger + per-cap tests + halt (A2, A3, A7) first, then rewire sites (A5) behind the
  single-site test (A6); B in parallel.

## C. Order and owners tonight
R0-baseline tag (integrator; needs user line) → A (worker W-R1) and B (worker W-R2) in parallel from 318b22a →
VERDICT by integrator successor → INTEGRATE under policy/1 → release/1 to Ops.
