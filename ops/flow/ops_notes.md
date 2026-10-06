# Ops_baseline notes (fixed size; overwrite, do not append history)
session: session_01MuXcCLZm3KXYyDj9v8HqyB (lineage 8/8, cannot create sessions). baseline 01UafTvm. Dev session_01Vtf8JhoPbyf3o8v87LPVLb (confirmed by baseline). Watcher told Ops directs it. Shadow: no model call in shadow decisions (O2); GA56 fixes cap count. Hourly routine still bound to baseline.
inbox seen up to: ops 20261006T212227 (DEV-ST-2o: INC-OPS-1 decided — integrator stays through GA52 r2 + R0 verdicts, GA52/GA57 archive after current item; R0a blocked on GA53 director confirm (baseline/user); R0b,R0c acting).
OPS-R0 done 21:2x: ops/flow/measure/R0.json by ops/hub/measure_r0.py (static: list_sessions + ga-mailbox shadow rows + baseline_verdicts).
  cost 10-06 UTC: 110.8 USD / 10.9 wall-h = 10.2 USD/h. per class USD/h: hub 6.08, worker 4.57, integrator 1.15, watcher 0.51. cache_read dominates (hub 16.3M/h).
  shadow gate 0/10: 25 compared, 0 agree, 0 false accepts, 40 baseline rows missing in shadow; every shadow decision ASK_HUMAN (judge_class failure); newest shadow row 07:18Z (daily_turns 40 cap, resumes 10-07 00:00Z).
  62 env fails: rlo missing; per-test list owed by DEV-R0c; ga-sdk tests not runnable here (auto-mode denies running external code).
sent: B-R0 21:17; INC-OPS-1 (dev ctx caps) + ST-OPS-2 21:21; B-TKG13 21:2x. Watcher now session_01X47ETY7Sx9hpAefj8vC28B (routine trig_012iYV3o :49), old archived. Ops successor: baseline asking user (depth-0).
next: each hourly fire also run `python3 ops/hub/shadow_digest.py digest` (OPS-SH1; routine prompt not editable at depth 8). OPS-R1 values with DEV-R1 once R0 lands; verify each release/1.
