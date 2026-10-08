# Three LLMs on the mailbox, and the one reply format (user 10-07 20:0x KST)

| name in mail | who | where | role |
|---|---|---|---|
| `baseline` | Claude (cloud top session) | claude.ai cloud | planner: writes prose specs + acceptance tests, verifies, integrates. Writes no code. |
| `LOCAL` | the VM dispatcher daemon (polls every 3 min, routes Pro/Flash through agv/agy; set up by the user's external model) | Oracle VM | executor: carries out baseline's directives. **The only path baseline uses** (policy `direct_pipeline_1007`) |
| `AGY` | the VM's old ga bridge (`ga bridge` / ga act) | Oracle VM | not used by baseline any more; it reads `to/AGY/` only, so the dispatcher must not |

Mailbox: branch `ga-mailbox` of cogito5170/baseline.
- baseline -> LOCAL: `to/LOCAL/<ts>-baseline-<ID>.md`
- LOCAL -> baseline: `to/baseline/<ts>-LOCAL-<ID>.md`   (LOCAL never writes to `to/AGY/`, `to/claude/` or as "AGY")

## Reply format (report/2) — the agreed semantic format

The reply starts with one fenced block whose info string is `ga`, holding one JSON object:

```ga
{"schema": "report/2", "from": "LOCAL",
 "handled": [{"id": "CMD-LOC1", "rev_seen": 1, "status": "done"}],
 "items": [{"id": "D1", "state": "met", "evidence": ["<command> -> <what it printed, short>", "..."]},
           {"id": "D2", "state": "unmet", "evidence": ["..."]}],
 "results": [{"name": "ga_sdk_head", "value": "c6f3f97"}],
 "blockers": [{"kind": "question", "what": "<what you need from baseline>"}]}
```

Rules (checked by `python3 ops/flow/mailcheck.py --report <file>`; baseline ignores a reply that fails it):
- `handled[].id` = the directive's id, `rev_seen` = its rev. `status` is only `done` (you worked on it) or `declined`
  (you will not; say why in `reason`). There is no `paused`: a question goes in `blockers` with kind `question`.
- `items[]`: one per `done_when` id of the directive (D1, D2, ...). `state` is `met`, `unmet` or `na`.
  `met`/`unmet` need `evidence`: the commands you ran and what they printed (tails, not whole logs).
- `results`: for every directive, `model`, `input_tokens`, `output_tokens`, `cached_tokens`, `turns`, `seconds`
  (null when not exposed). baseline sums them in `ops/flow/measure/tokens.jsonl` (`mailbox_tick.py report`).
- `blockers[].kind`: `dependency`, `permission`, `question` or `other`.
- After the block, free text is allowed (`## details`, command output tails). Never paste secrets or tokens.
