# Dev_baseline notes (fixed size; overwrite, never append history)
hub: session_01EqmaVLL6vWPFnmAqv9UKWH (Dev 10-07 01:2x~; prev 01VMbRhM) · baseline top 016tT1vv · Ops successor 013aqrQG (old 01M4vGeV)
OVERNIGHT (DEV-OVERNIGHT, policy.json overnight_delegation until 09:00 KST): baseline approves designs after Ops opinion; status/1 every 2h, final 08:30 KST; hourly self check-in via send_later (re-arm it in the successor; old trig_014GXkyw fires into the OLD hub)
integration: ga-sdk claude/gracious-meitner-vp49xe head 318b22a (evidence docs/R0_BASELINE.md) on tested 8ead789 = R0a+R0b+R0c, 1411/0/1 refenv; R0 = 318b22a until tag; tag R0-baseline = morning list (user line in an integrator session)

## Workers (all ga-sdk, base 318b22a unless noted; report ONE line to Dev; never integrate)
- W-R1 01KiyVDj  claude/DEV-R1-GW   VI-02(+03,07): gateway ga/llm, caps from policy (applies/windows keys), halt, ledger+policy hash, reconciliation, rule cache key incl sha/model/policy, rewire sites, single-site test, per-cap tests, `ga llm report --hour`
- W-R2 01QEjaAW  claude/DEV-R2-DRY  VI-04: `ga verdict --dry-run` (pure function, no model import test) + replay of baseline ops/hub/baseline_verdicts.jsonl (agree/disagree/not_reproducible/flaky)
- worker-R0a 015U1Lfq claude/DEV-VMSHA (base 277945de) VI-01: VM reports SHA per change + on ask; R0 tests result in repo; land BEFORE/with R1 integrate
- W-VI 01CnLoJD  claude/DEV-VI-06a-20  VI-06a notify/1 kind alert; VI-20 bridge unit -> ga bridge (no ~/baseline path)
- worker-GA52 01FUssZm (227k) CMD-GA52 rev2 (innerHTML + negative _num) -> on report: archive (user allowed archive)
- integrator 01Wz1byr: ready, refenv venv /root/.cache/ga-refenv; send VERDICT <id> <branch> <sha> per report, then INTEGRATE under policy/1 (auto_integrate extended to Dev hub id — successor: baseline must extend it to the new Dev id; user words needed)
- token-integrator 01FynfJT: CMD-TKG13 r2 resent to AGY (ga-mailbox 6514430, D1 edit change); AGY needs user "check mail" on the Mac

## Next steps
1. On each worker report: VERDICT via integrator -> record verdict in ops/hub/baseline_verdicts.jsonl -> INTEGRATE (ff/clean merge, full suite, mutations) -> release/1 to Ops (flow.py dev->ops) with sha.
2. Order: VMSHA (VI-01) before R1 integrate (or bump version); VI-06a before VI-05 watcher.
3. Next build group after these: VI-03, VI-05, VI-06, VI-07 (research/VM_INTERIOR_DESIGN.md §12); ask baseline for capacity.
4. Later VERDICT queue: GA52 r2, GA53 49f24c3 (worker 01HKHSLN idle), GA54 364680d (p2,p3 survived), GA56 c10675e, GA57 46687db (1381/0/56, 31/31).

## Designs (approved by baseline under overnight_delegation)
- research/VMHUB_DESIGN.md r2 (build HELD) · research/R1R2_DESIGN.md r3 · research/VM_INTERIOR_DESIGN.md r2 (acda708; §13 user questions Q1-Q6,Q8,Q9 = morning list)
- ASK-VM-COST answered (OP-DEV-VM-COST); vm_budget set by user in policy.json

## Rules / gotchas
- send only via ops/flow/flow.py + doorbell {"flow":"<path>"}; status ids must be unique (use DEV-ST-<MMDD-HHMM>)
- platform classifier refuses: relaying the user's words from another session to a worker (Instruction Poisoning) — ask the user to type in that session; archive needs explicit user OK in Dev session (given 00:5x)
- the user allowed git + send_message + archive in Dev 01EqmaVL (10-07 01:3x KST, own line); a successor must get its own user line; auto_integrate.dev_hub = 01EqmaVL since policy 8c01da6 (user words in top baseline)
- suite 15-20 min: workers/integrator run it in background with nohup + done marker
