# Dev_baseline notes (fixed size; overwrite, never append history)
hub: session_01VMbRhMjtfPAALfLjAWJ1tT (Dev, since 10-07 00:0x KST) · baseline top 016tT1vv · Ops 01M4vGeV
OVERNIGHT (DEV-OVERNIGHT, until 09:00 KST): baseline approves designs after Ops opinion; status/1 every 2h, final 08:30; hourly self check-in via send_later
integration: ga-sdk head 318b22a (evidence) on tested 8ead789 = R0a+R0b+R0c, 1411/0/1 refenv; tag R0-baseline pending user line in old integrator 01LBoWy9 · policy/1 extended to this hub (ad21638)

## Items (state)
- DEV-R0FREEZE  verdict ACCEPT 8ead789 (481d593); branch pushed 318b22a; TAG pending (user line; my relay refused as Instruction Poisoning)
- W-R1 01KiyVDj  DEV-VMAUTO+VMBUDGET gateway, claude/DEV-R1-GW from 318b22a (design research/R1R2_DESIGN.md §A,§A' approved)   ACTING
- W-R2 01QEjaAW  DEV-R3-DET dry-run + replay, claude/DEV-R2-DRY from 318b22a (§B)                                             ACTING
- worker-R0a 015U1Lfq  DEV-VMSHA claude/DEV-VMSHA from 277945de (land before/with R1)                                             ACTING
- integrator successor 01Wz1byr: told state, prepare refenv, wait for VERDICT; old 01LBoWy9 -> archive after tag
- CMD-GA52 r2 (01FUssZm) ACTING -> archive after report; CMD-TKG13 r2 SENT (ga-mailbox 6514430), AGY needs "check mail"
- DEV-VMDESIGN (R4): full VM interior design tonight -> Ops opinion -> baseline approval   TODO (extend research/VMHUB_DESIGN.md)
- awaiting VERDICT later: GA52 r2, GA53 49f24c3, GA54 364680d, GA56 c10675e, GA57 46687db
- HELD: VMHUB build

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
