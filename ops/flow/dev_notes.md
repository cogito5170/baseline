# Dev_baseline notes (fixed size; overwrite, never append history)
hub: session_01Vtf8JhoPbyf3o8v87LPVLb (Dev) · baseline 01UafTvm · Ops 01MuXcCLZm3KXYyDj9v8HqyB
integration: ga-sdk claude/gracious-meitner-vp49xe (f9671da 0.18.1 at 21:1x)

## Items (state)
- DEV-R0a served model = final-turn model      -> worker-R0a 015U1LfqNoymrTP9Wduzmh31 (fresh, baseline-prompted), claude/DEV-R0a   ACTING; GA53 idle_unredirected
- DEV-R0b router can descend rungs              -> worker-GA56 01HurcnH, branch claude/DEV-R0b   ACTING
- DEV-R0c reference env, full suite green       -> worker-GA57 01H2PH8B, branch claude/DEV-R0c   ACTING (251k: retire after)
- in-flight GA52 r2                             -> worker-GA52 01FUssZm (finish r2)              ACTING
- VERDICT queue -> ga-sdk-integrator 01LBoWy9: GA52 r2, then R0 in Ops B-R0 order R0c > R0a > R0b (all parallel); each landed -> release/1 to Ops
- DEV-TKG13: ACCEPT acf7352; INTEGRATE blocked (relayed approval denied by my permission check) -> user types push line in token-integrator
- R1..R5: PLANNED, start after R0 lands (R1 thin gateway+budgets first)

## Rules in force
- send only via ops/flow/flow.py; doorbell {"flow":"<path>"}
- integration still needs user push line in integrator session (R3 not live)
- workers report: {"id","branch","sha","tests","mutations":[{id,file,find,replace,tests}]}

## Pending
- POLL-RUNTIME opinions: GA57 in (gateway: lift ga/ops/core.py batch/tune into ga.llm; 6+ direct backends.create sites; served-model check + error labels in gateway; rule expiry; per-caller tune keys). GA52, GA53 pending -> one opinion/1 to baseline.
- done awaiting verdict (re-merge after GA52 lands): GA53 49f24c3, GA54 364680d (p2,p3 survived), GA56 c10675e, GA57 46687db. Release order GA52->53->54->55->56->57 (Ops may re-batch).
- integrator 01LBoWy9 ack: head f9671da, venv rlo 0.11.1.
- INC-OPS-1: integrator stays through R0; successor built from R0c recipe. GA52/GA57 archive after current item.
- successors (integrator after R0c, 2 R1 workers): send baseline status/1 kind successor_needed when due
- DEV-SH1 (R4 shadow-on-rejection): PLANNED after R1 gateway
