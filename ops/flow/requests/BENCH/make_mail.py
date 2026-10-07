"""Model bench at real task difficulty (user 10-07 15:1x: "셋이 동일한 task", "추론도 중요하니깐, 실제로 줄 task
난이도로 줘"). The same two real orders go to three worker models, each on the code from before that order landed:
  T1 = CMD-VIJ10 rev 2 (G3; edit list: paste-level, 2 files + gendoc)      base vm/BENCH-B1 = 0547772
  T2 = CMD-VI5 rev 2   (G2; rules in prose, the model writes the code)      base vm/BENCH-B2 = 19dc227
Ids CMD-BENCHA<k> (T1) and CMD-BENCHB<k> (T2), k = model below. Reference runs: T1 gemini-3.7-flash-medium 3 turns
8,756 tokens; T2 claude-sonnet-5-5-medium 3 turns 24,099 tokens. The agv branches these push are bench output only.
    python3 make_mail.py <mailbox worktree> [C]   (C = T2 rev 2 only, with the import-origin probe)
"""
import importlib.util
import json
import re
import sys
from datetime import datetime, UTC
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODELS = {1: "gpt-oss-120b-medium", 2: "gemini-3.7-flash-medium", 3: "gemini-3.6-flash-medium"}
WHY = "User 10-07 15:1x: compare three worker models on the same real-difficulty order (bench; never merged)."


def _load(group):
    sp = importlib.util.spec_from_file_location(f"mk_{group}", HERE.parent / group / "make_mail.py")
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def _rewrite(text, new_id, model, base):
    head_s, rest = text.split("\n```", 1)
    head = json.loads(head_s.split("\n", 1)[1])
    old = head["id"]
    head.update(id=new_id, rev=1, model=model, why=WHY)
    head.pop("changes", None)
    head["done_when"][0]["text"] = head["done_when"][0]["text"].split(" (rev ")[0]
    rest = rest.replace(f'"base": "claude/gracious-meitner-vp49xe"', f'"base": "{base}"').replace(old, new_id)
    return "```ga\n" + json.dumps(head, ensure_ascii=False) + "\n```" + rest


PROBE = ('"""Bench guard: the module under test must come from this worktree, not from the editable install of the '
         'deployed ga-sdk (10-07 15:3x: T2 rev 1 passed with no work because ga.watch resolved to ~/ga-sdk)."""\n'
         'from pathlib import Path\n\n\ndef test_watch_comes_from_the_worktree():\n'
         '    import ga.watch as W\n    assert Path(W.__file__).resolve().is_relative_to(Path.cwd().resolve()), W.__file__\n')


def _guard(text):
    """T2 rev 2 (ids CMD-BENCHC<k>): add the import-origin probe as a given test and to the test command."""
    pre, act = text.split("```ga-act\n", 1)
    spec_s, post = act.split("\n```", 1)
    spec = json.loads(spec_s)
    spec["tests"]["tests/test_bench_origin.py"] = PROBE
    spec["commands"]["commands"]["test"].append("tests/test_bench_origin.py")
    return pre + "```ga-act\n" + json.dumps(spec, ensure_ascii=False) + "\n```" + post


def items_c():
    g2 = _load("G2")
    t2 = g2.directive(next(i for i in g2.ITEMS if i["id"] == "CMD-VI5"))
    return [(f"CMD-BENCHC{k}", _guard(_rewrite(t2, f"CMD-BENCHC{k}", m, "vm/BENCH-B2"))) for k, m in MODELS.items()]


def items():
    g2, g3 = _load("G2"), _load("G3")
    t1 = g3.directive(next(i for i in g3.ITEMS if i["id"] == "CMD-VIJ10"))[1]
    t2 = g2.directive(next(i for i in g2.ITEMS if i["id"] == "CMD-VI5"))
    out = []
    for k, m in MODELS.items():
        out.append((f"CMD-BENCHA{k}", _rewrite(t1, f"CMD-BENCHA{k}", m, "vm/BENCH-B1")))
        out.append((f"CMD-BENCHB{k}", _rewrite(t2, f"CMD-BENCHB{k}", m, "vm/BENCH-B2")))
    return out


if __name__ == "__main__":
    box = Path(sys.argv[1])
    for i, text in (items_c() if sys.argv[2:] == ["C"] else items()):
        assert re.match(r"^CMD-([A-Z]+)(\d+)$", i), i
        ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
        (box / "to" / "AGY" / f"{ts}-baseline-{i}.md").write_text(text, encoding="utf-8")
        print(i)
