# Dev_baseline notes (fixed size; overwrite, never append history)
hub: session_01Vtf8JhoPbyf3o8v87LPVLb (Dev) · baseline 01UafTvm · Ops id: pending from baseline
integration: ga-sdk claude/gracious-meitner-vp49xe (f9671da 0.18.1 at 21:1x)

## Items (state)
- DEV-R0a served model = final-turn model      -> worker-GA53 01HKHSLN, branch claude/DEV-R0a   DISPATCHED
- DEV-R0b router can descend rungs              -> worker-GA56 01HurcnH, branch claude/DEV-R0b   DISPATCHED
- DEV-R0c reference env, full suite green       -> worker-GA57 01H2PH8B, branch claude/DEV-R0c   DISPATCHED
- in-flight GA52 r2                             -> worker-GA52 01FUssZm (finish r2)              ACTING
- VERDICT queue                                  -> ga-sdk-integrator 01LBoWy9 (GA52 r2, then R0a/b/c)
- token-integrator 01FynfJT: TKG13 continues; no R0 work
- R1..R5: PLANNED, start after R0 lands (R1 thin gateway+budgets first)

## Rules in force
- send only via ops/flow/flow.py; doorbell {"flow":"<path>"}
- integration still needs user push line in integrator session (R3 not live)
- workers report: {"id","branch","sha","tests","mutations":[{id,file,find,replace,tests}]}
