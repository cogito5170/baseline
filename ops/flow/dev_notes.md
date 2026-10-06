# Dev_baseline notes (fixed size; overwrite, never append history)
hub: session_01VMbRhMjtfPAALfLjAWJ1tT (Dev, since 10-07 00:0x KST) · baseline top 016tT1vv · Ops 01M4vGeV
integration: ga-sdk claude/gracious-meitner-vp49xe 277945de (R0a+R0b, 0.18.1) · policy/1 extended to this hub (ad21638)

## Items (state)
- DEV-R0FREEZE  -> integrator 01LBoWy9: merge R0c 78d8c69, refenv suite, docs/R0_BASELINE.md, push, tag R0-baseline (tag: user line)   ACTING
- DEV-VMSHA     -> worker-R0a 015U1Lfq, claude/DEV-VMSHA from 277945de; VERDICT after R0-baseline                                     ACTING
- CMD-GA52 r2   -> worker-GA52 01FUssZm (approved innerHTML check + negative _num); archive after report                               ACTING
- CMD-TKG13 r2  -> resent with changes(D1 edit), ga check clean, ga-mailbox 6514430 to/AGY/20261006T155710Z; await AGY report/2 -> token-integrator 01FynfJT VERDICT   SENT
- awaiting VERDICT after R0-baseline: GA52 r2, GA53 49f24c3 (worker 01HKHSLN idle), GA54 364680d (p2,p3 survived), GA56 c10675e, GA57 46687db (1381/0/56, 31/31)
- R1..R5 after R0-baseline: R1 = DEV-VMAUTO gateway + budgets + DEV-WATCH; DEV-R3-DET; DEV-BASEAUTO (R5); DEV-FORMATS (R4)
- HELD: DEV-VMHUB rev3 (needs token problem solved by measurement + R0-baseline)

## Sessions / INC-OPS-2,3
- archived 10-07 00:5x (user OK): worker-GA57 01H2PH8B; old dev hub 01Vtf8Jh already archived
- integrator 01LBoWy9 (230k): replace right after R0-baseline; successor from ops/hub/successors/ga_sdk_integrator.md + refenv; ask baseline
- GA52 (227k): archive after r2 report

## Rules in force
- send via ops/flow/flow.py + doorbell {"flow":"<path>"}; git + send_message allowed by user in this session (10-07 00:5x)
- INTEGRATE per policy/1; new refs (tags) need a user line in the integrator
- worker report: {"id","branch","sha","tests","mutations":[{id,file,find,replace,tests}]}

## Sent
- DEV-ST-1, DEV-ST-2 (baseline, direct); DEV-ST-OPS-1 (ops); OP-DEV-VM-COST opinion/1 (ASK-VM-COST) to baseline
