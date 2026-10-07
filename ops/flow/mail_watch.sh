#!/bin/bash
# Wake baseline only when new mail arrives (user 10-08 06:1x KST: the VM dispatcher's 1-minute silent poll, applied
# to Claude too). Polls ga-mailbox every WATCH_EVERY_S (60) seconds with git only — no model, no tokens — and exits
# (printing the new file names) as soon as to/baseline/ holds a LOCAL report that ops/flow/measure/tick_state.json has
# not seen. Run in the background; its exit re-invokes the session, which runs mailbox_tick.py.
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)" || exit 2
every=${WATCH_EVERY_S:-60}
while true; do
  git fetch -q origin ga-mailbox 2>/dev/null
  new=$(git ls-tree --name-only origin/ga-mailbox to/baseline/ | grep -- '-LOCAL-' | python3 -c '
import json, sys
seen = set(json.load(open("ops/flow/measure/tick_state.json")).get("seen", []))
for line in sys.stdin:
    n = line.strip().rsplit("/", 1)[-1]
    if n and n not in seen:
        print(n)')
  if [ -n "$new" ]; then echo "NEW MAIL:"; echo "$new"; exit 0; fi
  sleep "$every"
done
