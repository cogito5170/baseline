"""ISO-1: ga act runs a worktree's tests on the worktree's code only (defect found by the model bench, 10-07 15:3x).
Same pattern as G3 (goal carries the exact ga act actions; worker pastes them in turn 1), worker gemini-3.7-flash-medium
(policy spec_split.bench_1007). Base = integration 222ca6a.
    python3 make_mail.py <mailbox worktree>
"""
import importlib.util
import json
import re
import sys
from datetime import datetime, UTC
from pathlib import Path

HERE = Path(__file__).resolve().parent
_sp = importlib.util.spec_from_file_location("g3", HERE.parent / "G3" / "make_mail.py")
G3 = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(G3)
G3.HERE = HERE  # actions/ and tests/ of this directory
G3.WHY = ("10-07 15:3x model bench: on the VM the editable install of the deployed ga-sdk lets a worktree test import "
          "a missing ga.* module from ~/ga-sdk, so a test can pass on deployed code. Fix before group 4 (policy "
          "away_mode: VM fixes what it can).")
G3.PASTE = G3.PASTE.replace("ga-sdk 0547772", "ga-sdk 222ca6a")

ITEM = dict(id="CMD-ISO1", vi="ISO-1", model="gemini-3.7-flash-medium", test="test_act_isolation.py",
            files=["ga/act/commands.py", "ga/__init__.py"],
            guards=["tests/test_ga38.py", "tests/test_ga41.py", "tests/test_ga42_actions.py", "tests/test_vm_bridge_act.py"],
            goal=("ga act sets GA_ACT_ISOLATE in the command environment and ga/__init__ drops the editable-install "
                  "finders when it is set; rules: docstring of tests/test_act_isolation.py. " + G3.PASTE
                  + G3.actions("CMD-ISO1")),
            title="ISO-1 ga act test isolation from the deployed editable install")

if __name__ == "__main__":
    head, text = G3.directive(ITEM)
    G3.check(ITEM, head, text)
    assert re.match(r"^CMD-([A-Z]+)(\d+)$", ITEM["id"])
    box = Path(sys.argv[1])
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    (box / "to" / "AGY" / f"{ts}-baseline-{ITEM['id']}.md").write_text(text, encoding="utf-8")
    print(ITEM["id"], ITEM["guards"])
