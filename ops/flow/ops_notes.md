# Ops_baseline notes (fixed size; overwrite, do not append history) — handoff 10-07 03:2x KST
Ops: session_013aqrQGg4d1hyd3uyDVG7kM (since 01:22 KST; prev 01M4vGeV, 01Qhj1TX) — ctx 148k at 03:19, successor_needed sent (ST-OPS-16).
baseline: session_01KvzrDZZJDxYhbkb9Yb8LKs (since 04:4x KST, user-opened; prev 016tT1vv) (ctx 369k). Dev hub: session_01EqmaVLL6vWPFnmAqv9UKWH (ctx 206k, also successor_needed; handoff ops/hub/roles/DEV_BASELINE.md).
Watcher: session_01TBHcmu5ar3uwnjL7m6NhYg (Haiku; wake trig_01EFFxRB :49 KST).
Routines owned by Ops (rebind both to the successor: create self-bound copies with the same prompts, disable these, update assign.json):
  trig_01GcyujoR3XoM2PeoHe4iu2j hourly :19 UTC-minute (prompt has the full tick)
  trig_012F2ySDoB4v1nDYxhi5PHhT one-shot 10-07 08:30 KST final OPS-OVERNIGHT status/1
inbox seen up to: ops 20261007T011653 (none newer at 04:19). Last sent: baseline ST-OPS-17 (04:2x, stand-down question). User 04:0x: stop previous sessions, hand Dev/Ops to VM; top archived Dev; 08:30 trig_012F2ySD disabled by top; hourly disable refused by platform (do not route around).
Pushes: user 10-07 00:4x "push는 앞으로도 바로 해도 돼" -> push directly. Doorbell = send_message {"flow":"<path>"}.
Cheap tick: list_sessions via a Haiku subagent writing scratchpad sessions.json (keeps hub ctx low); measure_hourly.py tick; cloud_snapshot.py; shadow_digest.py digest.

## Open
- OPS-OVERNIGHT (until 09:00 KST): opinion/1 per Dev design within 1 round; verify/1 or incident/1 per release/1 within 1 round; hourly stalled list -> status/1;
  final status/1 08:30 (what landed, budget vs caps from measure/hourly.jsonl, MORNING_OPS.md). No release/1 has reached Ops yet tonight.
- Opinions sent overnight: OP-OPS-VMHUB-R3 (01:04), OP-OPS-R1R2 (01:07), OP-OPS-VMINT (01:18). Dev designs pending opinion: none.
- Verdicts ACCEPT, not integrated (INTEGRATE refused by platform classifier; morning item 8): DEV-VI-06a-20 87e3243, DEV-R1-GW 3e7ab1c, DEV-VMSHA bb443ff.
  DEV-R2-DRY 451e980: 1 fail under concurrent load, solo rerun pending. R0-baseline tag at 318b22a done by user's AGY (unverified by Ops: no ga-sdk access).
- OPS-R0FREEZE: on VMSHA integrate+deploy, the VM reports SHA via notify/1 to baseline-ops on ga-mailbox (last mail 00:58 KST) -> fill measure/VM_BASELINE.json;
  mismatch or >2 h silence after a release -> incident/1.
- OPS-VMBUDGET: VM caps unmeasured (no vm_spend.json). Cloud: 03:19 row 5.41 USD/h total (02:19: 13.97; top baseline 5.14 > cap 2.0 then, 1.39 now).
  ctx breaches: INC-OPS-3 (old) + INC-OPS-4 (Dev hub 01EqmaVL, W-R1 — W-R1 archived since). Re-file only on new sessions.
- Idle, no open item: token-integrator 01FynfJT, GA52 01FUssZm (252k, archive candidate: user words), W-VI 01CnLoJD completed, GA53 01HKHSLN.
- OPS-VMHUB rev3 build HELD; OPS-VMAUTO/BASEAUTO/FORMATS wait on Dev releases. OPS-WATCH: retire Claude watcher after 24 h side-by-side with DEV-WATCH.
- Record the next handoff: python3 ops/hub/measure_hourly.py handoff ops 013aqrQG <new> <crossed_at> <ack_at>.
Limits: Ops may not run ga-sdk code in-container; never archive/redirect sessions without the user's words; platform refusals stop + report verbatim.
