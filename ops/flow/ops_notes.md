# Ops_baseline notes (fixed size; overwrite, do not append history) — handoff 10-07 01:2x KST
Ops: session_01M4vGeVjHtivZ5nKLDSmdED (prev 01Qhj1TX) — ctx 217k, successor_needed sent (ST-OPS-14).
baseline: session_016tT1vvrTFehVFzWzfgxcCV (prev 01Ltsebb). Dev: session_01VMbRhMjtfPAALfLjAWJ1tT (ctx 283k).
Watcher: session_01TBHcmu5ar3uwnjL7m6NhYg (Haiku; wake trig_01EFFxRB :49 KST; alarms as notify/1).
Routines owned by Ops (rebind both to the successor; record in assign.json):
  trig_018jUnT6xNGK5xNszk1o3EDn hourly :19 (prompt has the full tick; old trig_01GvC312 disabled)
  trig_017Lm4aTso73qxZ9Ud1AaQvU one-shot 10-07 08:30 KST final OPS-OVERNIGHT status/1
inbox seen up to: ops 20261007T011653. Last sent: baseline ST-OPS-14 (01:21). Pushes: user 10-07 00:4x "push는 앞으로도 바로 해도 돼" -> push directly.

## Open
- OPS-OVERNIGHT (until 09:00 KST, policy.json overnight_delegation): baseline approves Dev designs after Ops opinion/1.
  Ops: opinion per design within 1 round; verify/1 or incident/1 per release/1 within 1 round; hourly stalled list -> status/1;
  final status/1 08:30 (what landed, budget vs caps from measure/hourly.jsonl, MORNING_OPS.md). User-only items -> ops/flow/MORNING_OPS.md.
- Opinions sent: OP-OPS-VMHUB-R3 (01:04), OP-OPS-R1R2 (01:07), OP-OPS-VMINT (01:18, research/VM_INTERIOR_DESIGN.md). Dev took VMHUB points in.
- OPS-R0FREEZE (R0): ga-sdk integration 318b22a; R0-baseline candidate 8ead789 (docs/R0_BASELINE.md: 1411/0/1 refenv, 0.18.1); tag pending user line.
  VM silent since 10-06 20:26 KST (notice per version only). DEV-VMSHA = VI-01. On Dev release: confirm VM SHA, fill measure/VM_BASELINE.json
  (vm_confirmed_sha, vm_r0_tests); mismatch or >2 h silence after release -> incident/1.
- OPS-VMBUDGET (R1): measure_hourly rows carry budget{cap: value/limit/breach}, breaches, vm_baseline. VM caps null until VI-07 hourly
  gateway summary (-> measure/vm_spend.json). ctx_max now ignores completed sessions (fixed 01:2x).
- INC-OPS-3 (ctx/cost): integrator replaced (new 01Wz1byr); old 01LBoWy9, GA52, GA57, 01Vtf8Jh etc. await archive (user words, Dev session).
  Over cap now: Dev hub 283k (8.1 USD/h = 66% of burn), top baseline 250k, Ops 217k. Don't re-file per tick; re-file only new sessions.
- OPS-VMHUB rev3 (R4): plan ops/hub/OPS_VMHUB.md; build HELD until VMAUTO solved (user) + R0-baseline.
- OPS-VMAUTO (R1) / OPS-BASEAUTO (R5) / OPS-FORMATS (R4): accepted; wait on Dev releases (VI-02/03/07, DEV-BASEAUTO, VI-06a/06 registry).
  Formats: notify/1 ack+alert across the boundary is the Ops position (Q7 is Dev+Ops, not user).
- B-R1W-R3D / OPS-WATCH: on DEV-WATCH (VI-05) release, 24 h side-by-side vs Claude watcher; then status/1 to retire it + its routine.
- Handoffs to record (measure_hourly.py handoff ...): ops 01Qhj1TX->01M4vGeV (ack 00:19 KST); this one when the successor acks.
- Token: B-TKG13 ACCEPT acf7352 waits user 'TKG13 push' in Token integrator 01FynfJT.

## Hourly (trig_018jUnT6 prompt is authoritative)
0 inbox ops; 1 sessions (subagent: list_sessions 30 -> scratchpad sessions.json) + ops_rules.py; stalled list -> status/1;
2 ga-mailbox to/baseline-ops/-shadow (SHA notices, alerts); 3 shadow_digest.py digest; 3b measure_hourly.py tick sessions.json -> commit;
4 cloud_snapshot.py < sessions.json -> commit on change; 5 own ctx > 150k -> overwrite this file + successor_needed.
Limits: Ops may not run ga-sdk code in-container; measure statically. Never archive/redirect sessions without the user's words.
