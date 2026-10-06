# Ops_baseline notes (fixed size; overwrite, do not append history)
session: session_01MuXcCLZm3KXYyDj9v8HqyB (lineage 8/8, cannot create sessions). baseline 01UafTvm. Dev 01Vtf8Jh (seen in list; confirm via baseline).
inbox seen up to: ops 20261006T211343 (OPS-R0..R5).
OPS-R0 done 21:2x: ops/flow/measure/R0.json by ops/hub/measure_r0.py (static: list_sessions + ga-mailbox shadow rows + baseline_verdicts).
  cost 10-06 UTC: 110.8 USD / 10.9 wall-h = 10.2 USD/h. per class USD/h: hub 6.08, worker 4.57, integrator 1.15, watcher 0.51. cache_read dominates (hub 16.3M/h).
  shadow gate 0/10: 25 compared, 0 agree, 0 false accepts, 40 baseline rows missing in shadow; every shadow decision ASK_HUMAN (judge_class failure); newest shadow row 07:18Z (daily_turns 40 cap, resumes 10-07 00:00Z).
  62 env fails: rlo missing; per-test list owed by DEV-R0c; ga-sdk tests not runnable here (auto-mode denies running external code).
sent: batch/1 B-R0 (R0a,b,c parallel; order c,a,b) 21:17.
next: OPS-R1 values (budgets, batch cap, SLOs) -> spec/1 inside batch/1 with DEV-R1 once R0 lands; verify each release/1.
