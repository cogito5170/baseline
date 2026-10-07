#!/bin/bash
# Run one ACT1 prose spec with agy directly on the VM (no ga act), user 10-07 18:4x: "VM에서 agy 직접 실행으로 진행해".
# Baseline gives prose + its acceptance test only; the agy agent (gemini-3.1-pro-high) writes the code.
#   bash agy_direct.sh CMD-ACTB1     then     bash agy_direct.sh CMD-ACTR1
# Result: branch agv/<ID>-direct pushed to cogito5170/ga-sdk; baseline verifies and integrates.
set -euo pipefail
ID=${1:?usage: agy_direct.sh CMD-ACTB1|CMD-ACTR1}
MODEL=${MODEL:-gemini-3.1-pro-high}
REF=origin/claude/gracious-meitner-vp49xe
D=ops/flow/requests/ACT1
case "$ID" in
  CMD-ACTB1) TEST=test_bridge_act_turns.py; FILES="ga/bridge/act.py"
             RUN="tests/test_bridge_act_turns.py tests/test_vm_bridge_act.py" ;;
  CMD-ACTR1) TEST=test_act_reads.py; FILES="ga/act/loop.py ga/act/retrieve.py ga/act/card.py"
             RUN="tests/test_act_reads.py tests/test_ga38.py tests/test_ga41.py tests/test_ga45.py tests/test_ga47.py tests/test_act_isolation.py --deselect tests/test_ga38.py::Loop::test_ts_fixture_seeded_bug_fixed" ;;
  *) echo "unknown id $ID"; exit 2 ;;
esac
agy models | grep -q -- "$MODEL" || { echo "STOP: $MODEL not in 'agy models'"; agy models; exit 1; }
git -C ~/baseline fetch -q origin claude/gracious-meitner-vp49xe
WT=~/wt-$ID
cd ~/ga-sdk && git fetch -q origin vm/G4-INT
git worktree remove --force "$WT" 2>/dev/null || true
git worktree add -q -f -B "agv/$ID-direct" "$WT" origin/vm/G4-INT
cd "$WT"
git -C ~/baseline show "$REF:$D/tests/$TEST" > "tests/$TEST"
git -C ~/baseline show "$REF:$D/agy_direct/$ID.md" > /tmp/$ID.prompt.md
echo "== agy ($MODEL) on $ID in $WT"
agy --dangerously-skip-permissions --model "$MODEL" --prompt "$(cat /tmp/$ID.prompt.md)" || echo "(agy exited non-zero; checking the tests anyway)"
git -C ~/baseline show "$REF:$D/tests/$TEST" | cmp -s - "tests/$TEST" || { echo "STOP: the agent changed tests/$TEST"; exit 1; }
other=$(git status --porcelain | awk '{print $2}' | grep -vxF -e "tests/$TEST" $(printf -- '-e %s ' $FILES) || true)
[ -z "$other" ] || { echo "STOP: files outside the spec changed:"; echo "$other"; exit 1; }
# shellcheck disable=SC2086
~/ga-venv/bin/python -m pytest -q -p no:cacheprovider $RUN
git add "tests/$TEST" $FILES
git -c user.name="ga mail (VM)" -c user.email="ga-vm@localhost" commit -q -m "$ID: agy direct ($MODEL) from baseline prose spec"
git push -q -f origin "agv/$ID-direct"
echo "DONE $ID agv/$ID-direct = $(git rev-parse --short HEAD)"
