# Ops_baseline notes (fixed size; overwrite, do not append history) — handoff 10-06 23:3x KST
prev Ops: session_01MuXcCLZm3KXYyDj9v8HqyB (archived after successor ack). baseline: session_01LtsebbxyWz4BAggiGcG1WF (depth 0). Dev: session_01Vtf8JhoPbyf3o8v87LPVLb.
Ops sessions/routines (assign.json): token watcher session_01TBHcmu5ar3uwnjL7m6NhYg (Haiku, wake trig_01EFFxRB :49 KST, alarms come as notify/1);
  hourly Ops routine trig_01MtdLyUZwfJNqtzKyXLkxpb (prompt includes shadow digest + snapshot steps).
inbox seen up to: ops 20261006T232434 (OPS-WATCH). Last sent: dev batch B-R1W-R3D 23:25; baseline ST-OPS-7 23:26.

## Done
- OPS-R0: ops/flow/measure/R0.json via ops/hub/measure_r0.py (static, no ga code). 10.2 USD/wall-h (hub 6.08, worker 4.57, integrator 1.15, watcher 0.51 USD/h).
  Shadow gate 0/10 (0/25 agree, 0 false accepts, all shadow = ASK_HUMAN, no model call O2; VM daily_turns 40 cap, resumes 00:00Z).
  62 env fails = rlo missing; per-test list owed by DEV-R0c release (11 test files import rlo).
- OPS-SH1: ops/hub/shadow_digest.py (stage dev|ops|vm row -> pending; digest -> ONE shadow/1 when oldest >=60 min or blocks_chain). 0 rows so far.
- OPS-WATCH (in progress): ops/hub/watch_thresholds.json (ctx 150000, 5 USD/h session, 12 USD/h total, snapshot 2 h).
- B-TKG13: Dev verdict ACCEPT acf7352; waits for user 'TKG13 push' in Token integrator 01FynfJT.

## Open
- R0: DEV-R0a 759d873 + R0b b891bea ACCEPT, not integrated (Dev's INTEGRATE denied by its permission check; user unblock). R0c 78d8c69 built (1400 passed, REFENV.md). No release/1 reached Ops yet -> verify each on arrival.
- B-R1W-R3D: DEV-WATCH + OPS-LIMITS-WATCH || DEV-R3-DET. On DEV-WATCH release: verify on VM (notify-1 version), start 24 h side-by-side vs Claude watcher; every Claude alarm must also come from VM; then status/1 so baseline retires the Claude watcher + routine.
- OPS-R1 values (budgets, batch cap, SLOs) -> spec inside batch/1 with DEV-R1. OPS-R2..R5 later.
- INC-OPS-1 (Dev ctx caps) decided by Dev.

## Hourly (every fire)
1 inbox ops; 2 git fetch ga-mailbox (to/baseline, -ops, -shadow) -> scoring/incident if lag unexplained; 3 python3 ops/hub/shadow_digest.py digest;
4 snapshot EVERY hour (VM stale alarm at 2 h): subagent list_sessions 12 -> ops/hub/cloud_snapshot.py -> commit; 5 ops_rules.py on get_session obs when ctx matters.
Limits: Ops may not run ga-sdk code in-container (auto-mode denial); measure statically.
