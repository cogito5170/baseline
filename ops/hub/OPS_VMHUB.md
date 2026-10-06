# OPS-VMHUB — how Ops deploys, observes, measures and rolls back the VM Dev/Ops baselines (R4, shadow only)

Authority: the cloud Dev/Ops hubs stay the authority until a separate cutover spec. The VM baselines take no externally visible action.

## Deploy check
- Input: Dev's release/1 for DEV-VMHUB (repo cogito5170/Dev or cogito5170/Ops, sha).
- Pass: a VM->cloud status/1 names that sha as running version (protocol_version included). No cloud read of VM internals.
- Fail: no such status/1 within 2 h of the release, or a different sha -> incident/1 to Dev (kind deploy_mismatch).

## Observe (boundary only)
- Health: VM status/1 at least hourly; a gap > 2 h -> stale alarm (same rule as the snapshot, watch_thresholds.json).
- Incidents and rejections arrive as incident/1 / shadow/1; Ops scores them like the shadow gate (agree vs cloud decision).
- Duplicate request_id answered twice, or a reply without request_id -> incident/1 (kind boundary_violation).

## Measure
- VM baselines report tokens per episode in status/1 (input, output, cache_read, cache_write, model). Ops adds class `vm` to
  ops/flow/measure/ in the R0.json units (per hour: output, cache_read, cache_write, usd), next to the cloud hub figures.
- Budget: none runs a model continuously until the user sets one (ASK-VM-COST, Ops proposal OP-VM-COST: 2 USD/h, 30 USD/day).

## Rollback (cloud hubs stay authority throughout)
1. Any VM incident of kind boundary_violation, two_primaries, budget overrun, or lost/duplicated message after restart:
   Ops stops consuming VM messages (cloud ignores them; nothing external depended on them in shadow).
2. Ops sends incident/1 to Dev with evidence; Dev's fix comes back as a new release/1 -> deploy check again.
3. If the VM keeps sending: baseline asks the user to stop the VM baseline process; the cloud hubs continue unchanged.
4. No cloud state is changed by a rollback, because in shadow the VM wrote none.
