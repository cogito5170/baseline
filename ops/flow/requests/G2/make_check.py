"""Post-deploy checks of vm/G2-INT (0547772), user 10-07 12:3x: "성공했어. 확인 지시 보내".
    python3 make_check.py <mailbox worktree>   -> writes to/AGY/<ts>-baseline-<id>.md
CMD-GCK1: read-only ga supervise turn (bridge + forms registry path alive).
CMD-GCK2: ga act with a baseline test that runs `ga llm report --status` on the VM's own policy and ledger (VI-07).
"""
import json
import sys
from datetime import datetime, UTC
from pathlib import Path

HERE = Path(__file__).resolve().parent
WHY = "User 10-07 12:3x deployed group 2 (ga-sdk vm/G2-INT 0547772) on the VM and asked for the post-deploy checks."


def c1():
    head = {"schema": "directive/2", "id": "CMD-GCK1", "rev": 1, "to": "AGY", "after": [],
            "goal": "Post-deploy check of vm/G2-INT (0547772): list the workdir and answer OK.", "why": WHY,
            "scope": [{"id": "S1", "text": "read-only: one list_dir on the workdir; no edits, no commits, no pushes"}],
            "done_when": [{"id": "D1", "text": "the answer starts with OK and lists the workdir's top-level entries"}],
            "budget": {"claude_p_runs": 0}, "model": "gemini-3.7-flash-low"}
    return "```ga\n" + json.dumps(head, ensure_ascii=False) + "\n```\n"


def c2():
    test = "test_g2c2_live_status.py"
    goal = ("Post-deploy check of VI-07: no code change is needed. The given test runs `ga llm report --status` on the "
            "VM's own policy and ledger. Run the test command once; when it passes, answer DONE. Do not edit any file.")
    head = {"schema": "directive/2", "id": "CMD-GCK2", "rev": 1, "to": "AGY", "after": [], "goal": goal, "why": WHY,
            "scope": [{"id": "S1", "text": "no file edits in a ga-sdk worktree; the test is baseline's"}],
            "done_when": [{"id": "D1", "text": "ga act ends done: tests/" + test + " passes on the VM"}],
            "budget": {"claude_p_runs": 0}, "model": "gemini-3.7-flash-low"}
    spec = {"item": {"id": "CMD-GCK2", "goal": goal, "files": [], "done_when": "test"},
            "tests": {f"tests/{test}": (HERE / "tests" / test).read_text(encoding="utf-8")},
            "commands": {"commands": {"test": ["{python}", "-m", "pytest", "-q", "-s", "-p", "no:cacheprovider",
                                               f"tests/{test}"]}, "timeout_s": 300},
            "base": "claude/gracious-meitner-vp49xe", "repo": "ga-sdk"}
    return ("```ga\n" + json.dumps(head, ensure_ascii=False) + "\n```\n\n```ga-act\n"
            + json.dumps(spec, ensure_ascii=False) + "\n```\n")


if __name__ == "__main__":
    import re
    for t in (c1(), c2()):  # rev 1 as CMD-G2C1/2 was declined: ids are CMD-<letters><number> (ga.forms DIRECTIVE_ID_RE)
        assert re.match(r"^CMD-([A-Z]+)(\d+)$", json.loads(t.split("\n")[1])["id"])
    box = Path(sys.argv[1])
    for i, text in (("CMD-GCK1", c1()), ("CMD-GCK2", c2())):
        ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
        p = box / "to" / "AGY" / f"{ts}-baseline-{i}.md"
        p.write_text(text, encoding="utf-8")
        print(p.name)
