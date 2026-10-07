"""Baseline side of the agy direct bridge (ops/agy_bridge/direct_bridge.py): build one to/AGY-direct task, no ga on either side.

    python3 ops/flow/agytask.py <mailbox worktree> <ID> <rev> <model> <repo> <base> <prompt.md> <files,comma> \
        <test.py[,test2.py]> [extra pytest args...]

The prompt is prose (checked by nocode); the tests are baseline's acceptance tests, written into tests/<name> on the
VM and verified byte-identical after agy ran. The model must be in ops/vm/agy_models.txt (`agy models`).
"""
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mailcheck  # noqa: E402
import nocode  # noqa: E402


def build(id_, rev, model, repo, base, prompt, files, tests, extra):
    if not re.fullmatch(r"CMD-[A-Z]+\d+", id_):
        raise SystemExit(f"id {id_!r}: must be CMD-<LETTERS><number>")
    if model not in mailcheck.KNOWN_MODELS:
        raise SystemExit(f"model {model!r} not in agy models (ops/vm/agy_models.txt)")
    if repo not in ("ga-sdk", "token") or not files or not tests:
        raise SystemExit("repo must be ga-sdk|token; files and tests are required")
    errs = nocode.text_problems("prompt", prompt)
    if errs:
        raise SystemExit("prompt carries code: " + "; ".join(errs))
    t = {f"tests/{Path(p).name}": Path(p).read_text(encoding="utf-8") for p in tests}
    head = {"schema": "agy-task/1", "id": id_, "rev": int(rev), "model": model, "repo": repo, "base": base,
            "files": files, "tests": t, "run_extra": " ".join(extra), "branch": f"agv/{id_}-r{rev}"}
    return "```agy-task\n" + json.dumps(head, ensure_ascii=False) + "\n```\n\n" + prompt.strip() + "\n"


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 9:
        raise SystemExit(__doc__)
    box, id_, rev, model, repo, base, prompt, files, tests, *extra = a
    text = build(id_, rev, model, repo, base, Path(prompt).read_text(encoding="utf-8"), files.split(","),
                 tests.split(","), extra)
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    out = Path(box) / "to" / "AGY-direct" / f"{ts}-{id_}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(out.name)
