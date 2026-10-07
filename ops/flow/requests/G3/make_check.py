"""Post-deploy checks of vm/G3-INT (222ca6a), user 10-07 14:5x: "배포완료했다".
    python3 make_check.py <mailbox worktree>   -> writes to/AGY/<ts>-baseline-<id>.md
CMD-GCK3: read-only ga supervise turn (bridge alive on the new code).
CMD-GCK4: ga act that runs the group 3 acceptance tests on the VM as deployed (no edit; files = one given test).
"""
import json
import re
import sys
from datetime import datetime, UTC
from pathlib import Path

WHY = "User 10-07 14:5x deployed group 3 (ga-sdk vm/G3-INT 222ca6a) on the VM; post-deploy checks."
TESTS = ["tests/test_vi04b_shadow_verdict.py", "tests/test_vi10a_journal.py", "tests/test_vi10b_machine.py",
         "tests/test_ga42_shadow.py", "tests/test_verdict.py"]
PROBE = '''"""Post-deploy probe of vm/G3-INT (baseline): the deployed tree carries group 3."""
import unittest
from pathlib import Path


class Deployed(unittest.TestCase):
    def test_group3_files_are_present(self):
        for p in ("ga/vm/journal.py", "ga/vm/machine.py", "tests/test_vi10b_machine.py"):
            self.assertTrue(Path(p).is_file(), p)
'''


def c3():
    head = {"schema": "directive/2", "id": "CMD-GCK3", "rev": 1, "to": "AGY", "after": [],
            "goal": "Post-deploy check of vm/G3-INT (222ca6a): list the workdir and answer OK.", "why": WHY,
            "scope": [{"id": "S1", "text": "read-only: one list_dir on the workdir; no edits, no commits, no pushes"}],
            "done_when": [{"id": "D1", "text": "the answer starts with OK and lists the workdir's top-level entries"}],
            "budget": {"claude_p_runs": 0}, "model": "gemini-3.7-flash-low"}
    return "```ga\n" + json.dumps(head, ensure_ascii=False) + "\n```\n"


def c4():
    probe = "tests/test_g3ck_probe.py"
    goal = ("Post-deploy check of group 3: no code change is needed. Run the test command once; when it passes, "
            "answer DONE. Do not edit any file.")
    head = {"schema": "directive/2", "id": "CMD-GCK4", "rev": 1, "to": "AGY", "after": [], "goal": goal, "why": WHY,
            "scope": [{"id": "S1", "text": "no file edits in a ga-sdk worktree; the tests are baseline's"}],
            "done_when": [{"id": "D1", "text": "ga act ends done: the group 3 acceptance tests pass on the VM base"}],
            "budget": {"claude_p_runs": 0}, "model": "gemini-3.7-flash-low"}
    spec = {"item": {"id": "CMD-GCK4", "goal": goal, "files": [probe], "done_when": "test"},
            "tests": {probe: PROBE},
            "commands": {"commands": {"test": ["{python}", "-m", "pytest", "-q", "-p", "no:cacheprovider", probe,
                                               *TESTS]}, "timeout_s": 600},
            "base": "claude/gracious-meitner-vp49xe", "repo": "ga-sdk"}
    return ("```ga\n" + json.dumps(head, ensure_ascii=False) + "\n```\n\n```ga-act\n"
            + json.dumps(spec, ensure_ascii=False) + "\n```\n")


if __name__ == "__main__":
    out = (("CMD-GCK3", c3()), ("CMD-GCK4", c4()))
    for _, t in out:
        assert re.match(r"^CMD-([A-Z]+)(\d+)$", json.loads(t.split("\n")[1])["id"])
    box = Path(sys.argv[1])
    for i, text in out:
        ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
        p = box / "to" / "AGY" / f"{ts}-baseline-{i}.md"
        p.write_text(text, encoding="utf-8")
        print(p.name)
