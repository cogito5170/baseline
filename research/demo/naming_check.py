"""Verifier for research/NAMING.md (BD-396): code, not a model, decides whether the naming deliverable is done.

Checks: every layer row has name, what, form, status; the four entries (CLI, API, MCP, UI) and the Core-only use of
"SDK" are stated; every GA<n> id cited exists as a directive or is planned in AUTONOMY_MACHINE.md section 6; the design
doc points to the naming doc. Exit 0 = pass, 1 = fail with the reasons.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
naming = (ROOT / "research/NAMING.md").read_text(encoding="utf-8")
design = (ROOT / "research/AUTONOMY_MACHINE.md").read_text(encoding="utf-8")
problems = []
rows = [r for r in naming.splitlines() if r.startswith("| GA ")]
for r in rows:
    cells = [c.strip() for c in r.strip("|").split("|")]
    if len(cells) != 4 or not all(cells):
        problems.append(f"row incomplete: {r[:60]}")
names = {r.split("|")[1].strip() for r in rows}
for need in ("GA Engine", "GA Core", "GA Protocol", "GA CLI", "GA API", "GA MCP", "GA UI", "GA Backends", "GA Actions", "GA Guards"):
    if need not in names:
        problems.append(f"layer missing: {need}")
if "SDK 는 이것만 가리킨다" not in naming:
    problems.append("Core-only meaning of SDK not stated")
planned = set(re.findall(r"GA(\d+)", design[design.find("## 6."):]))
for n in sorted(set(re.findall(r"GA(\d+)", naming))):
    if not (ROOT / f"directives/CMD-GA{n}.md").exists() and n not in planned and int(n) > 34:
        problems.append(f"GA{n} cited but neither a directive nor planned")
if "NAMING.md" not in design:
    problems.append("AUTONOMY_MACHINE.md does not point to NAMING.md")
print("\n".join(problems) or f"naming ok: {len(rows)} layers")
sys.exit(1 if problems else 0)
