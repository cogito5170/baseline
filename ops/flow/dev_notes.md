# Dev_baseline notes (fixed size; overwrite, never append history)
hub: session_01EqmaVLL6vWPFnmAqv9UKWH (Dev 10-07 01:2x~; over cap 158k, successor deferred to morning by baseline 02:23 — act on events only; successor_needed again at ~250k) · prev 01VMbRhM · baseline top 016tT1vv · Ops 013aqrQG
OVERNIGHT (policy.json overnight_delegation until 09:00 KST): status/1 every 2h, final 08:30 KST with morning list; hourly self check-in via send_later (01EqmaVL's trig_01JUyE96 fires ~02:25 into the OLD hub; successor re-arms its own)
policy: auto_integrate.dev_hub = 01EqmaVL (8c01da6) -> successor needs baseline to extend again (user words in top). R0-baseline tag target = ga-sdk 318b22a (e2455e8).
integration: ga-sdk claude/gracious-meitner-vp49xe head 318b22a (R0). Tag R0-baseline NOT created.

## PLATFORM REFUSALS (stop, report, never route around)
- 01:41 send_message Dev->integrator "INTEGRATE/TAG R0-baseline 318b22a": classifier "[Modify Shared Resources]"
- 02:02 send_message Dev->integrator "INTEGRATE DEV-VI-06a-20 87e3243": classifier "judged this action dangerous (no explanation)"
- VERDICT requests and doorbells go through. Every INTEGRATE/TAG -> morning list (user's own line in integrator 01Wz1byr, or a send_message permission rule).

## Pending INTEGRATE (morning list), all ga-sdk, base 318b22a
1. DEV-VI-06a-20 87e3243 ACCEPT (row 9a40fc1) — ff
2. DEV-R1-GW 3e7ab1c ACCEPT (row 502a042) — AFTER VI-01 VMSHA (order rule)
3. DEV-R2-DRY 451e980 ACCEPT (clean solo 1432/0/1) — ff
4. DEV-VMSHA bb443ff ACCEPT (branch 1418/0/1) — merge commit onto 318b22a; merged-tree suite requested 02:5x; must land BEFORE R1
5. tag R0-baseline -> 318b22a

## Sessions
- integrator 01Wz1byr: refenv /root/.cache/ga-refenv; doing R2 solo rerun
- W-R1 01KiyVDj: done (VI-02 accepted), archived by 01EqmaVL 02:2x (ctx 156k, INC-OPS-4)
- W-R2 01QEjaAW: done, idle (VI-04)
- W-VI 01CnLoJD: done, idle (87k) -> reuse for VI-06 (needs VI-06a integrated)
- worker-R0a 015U1Lfq claude/DEV-VMSHA VI-01: still acting, no report yet (176k at 01:24 — over cap; check)
- GA52 01FUssZm, GA53 01HKHSLN, token-integrator 01FynfJT: blocked/idle as before
## Follow-ups
- m9 dead guard in ga/llm/gateway.py (drop or seeded-cache test); hub.py:301 Runner adapters -> gateway (VI-03); ga/console/config.py:49,98 still ~/baseline bridge.py
## Next
- next build group {VI-03, VI-05, VI-06, VI-07} needs VI-02/VI-06a integrated -> blocked on INTEGRATE refusals; capacity via baseline status/1
- later VERDICT queue: GA52 r2, GA53 49f24c3, GA54 364680d, GA56 c10675e, GA57 46687db
## Rules
- send only via ops/flow/flow.py + doorbell {"flow":"<path>"}; status ids unique DEV-ST-<MMDD-HHMM>
- never relay the user's words to another session as approval; workers read policy.json themselves
- user allowed git + send_message + archive in Dev 01EqmaVL (01:3x); a successor must get its own user line
