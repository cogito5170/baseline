"""directive/2 form check that needs no ga-sdk clone (user 10-07 18:1x: "형식 문제 ... 정립해놔봐").

ga-sdk's ga/forms is the real validator (the VM bridge runs it). A baseline container often has no ga-sdk, and then
make_mail scripts skipped the check and the VM declined the mail. This module holds every hard rule the VM bridge has
declined baseline mail for (ga-mailbox to/baseline* reports, 10-05..10-07), so the pre-commit hook refuses such mail
before it is pushed:

  CMD-AG12, CMD-X0 x4   head is not directive/2 (kind/ref/from/... fields, wrong schema)
  CMD-PING6             $.why is required
  CMD-X0 x2 (10-07)     $.id must be CMD-<PREFIX><number>
  CMD-TKG13, CMD-ACTR1, CMD-ACTB1   $.changes is required when rev > 1 (METHOD rev 16 3.6)
  CMD-GCK2 rev 1        ga-act item files empty
  CMD-VB3               model not in agy models (deliberate test; models are checked against KNOWN_MODELS, warn only)

    python3 ops/flow/mailcheck.py <mail.md ...>   -> exit 1 and the reasons
    python3 ops/flow/mailcheck.py --self-test
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

BLOCK = re.compile(r"```(ga|ga-act)[ \t]*\n(.*?)\n```", re.S)
ID_RE = re.compile(r"^CMD-[A-Z]+[0-9]*$")
REQUIRED = ("schema", "id", "rev", "to", "goal", "why")
EXPECTED = ("scope", "done_when")  # every accepted mail has them; the VM has not declined for their absence
KNOWN = set(REQUIRED) | set(EXPECTED) | {"after", "budget", "model", "changes"}
CHANGE_OPS = {"add", "edit", "drop"}
# The model list is the VM's own `agy models` output (user 10-07 18:5x: "model은 agy models"), saved verbatim in
# ops/vm/agy_models.txt; refresh it by pasting the output there. The set below is the fallback until it exists.
AGY_MODELS_FILE = Path(__file__).resolve().parents[1] / "vm" / "agy_models.txt"
_FALLBACK_MODELS = {"gemini-3.7-flash-low", "gemini-3.7-flash-medium", "gemini-3.6-flash-medium",
                    "gpt-oss-120b-medium", "gemini-3.1-pro-high", "gemini-3.1-pro-low", "claude-sonnet-5-5-medium"}


def _agy_models() -> set[str]:
    try:
        text = AGY_MODELS_FILE.read_text(encoding="utf-8")
    except OSError:
        return set(_FALLBACK_MODELS)
    found = set(re.findall(r"\b([a-z][a-z0-9]*(?:[-.][a-z0-9]+)+)\b", text))
    return found or set(_FALLBACK_MODELS)


KNOWN_MODELS = _agy_models()


def problems(text: str) -> tuple[list[str], list[str]]:
    """(hard problems, warnings) of one to/AGY mail."""
    hard, warn = [], []
    blocks = {k: v for k, v in BLOCK.findall(text)}
    if "ga" not in blocks:
        return ["no ```ga head block"], warn
    try:
        h = json.loads(blocks["ga"])
    except ValueError as e:
        return [f"head is not JSON: {e}"], warn
    if h.get("schema") != "directive/2":
        hard.append(f"$.schema must be directive/2 (got {h.get('schema')!r})")
    for k in REQUIRED:
        if k not in h or h[k] in ("", [], None):
            hard.append(f"$.{k}: is required")
    for k in EXPECTED:
        if not h.get(k):
            warn.append(f"$.{k}: missing (every accepted mail carries it)")
    for k in set(h) - KNOWN:
        hard.append(f"$.{k}: unknown field")
    if not ID_RE.match(str(h.get("id", ""))):
        hard.append("$.id: must be CMD-<PREFIX><number> (letters then digits, no dash after the prefix)")
    rev = h.get("rev")
    if not isinstance(rev, int) or isinstance(rev, bool) or rev < 1:
        hard.append("$.rev: must be an int >= 1")
    elif rev > 1:
        ch = h.get("changes")
        if not ch:
            hard.append("$.changes: is required when rev > 1 (write only what changed)")
        else:
            for i, c in enumerate(ch):
                if not (isinstance(c, dict) and c.get("item") and c.get("op") in CHANGE_OPS and c.get("text")):
                    hard.append(f"$.changes[{i}]: needs item, op ({'/'.join(sorted(CHANGE_OPS))}) and text")
    for key in ("scope", "done_when"):
        for i, x in enumerate(h.get(key) or []):
            if not (isinstance(x, dict) and x.get("id") and x.get("text")):
                hard.append(f"$.{key}[{i}]: needs id and text")
    if h.get("model") and h["model"] not in KNOWN_MODELS:
        warn.append(f"$.model {h['model']!r} not seen on the VM yet (the bridge declines unknown models at no cost)")
    if "ga-act" in blocks:
        try:
            spec = json.loads(blocks["ga-act"])
        except ValueError as e:
            return hard + [f"ga-act block is not JSON: {e}"], warn
        item = spec.get("item") or {}
        if item.get("id") != h.get("id"):
            hard.append("ga-act item.id must equal the head id")
        if not item.get("files"):
            hard.append("ga-act item.files: is required (non-empty)")
        if not item.get("goal"):
            hard.append("ga-act item.goal: is required")
        if not spec.get("base"):
            hard.append("ga-act base: is required")
        if not spec.get("repo"):
            warn.append("ga-act repo: missing (bridge falls back to its configured repo)")
    return hard, warn


REPORT_STATUS = {"done", "declined"}
ITEM_STATE = {"met", "unmet", "na"}
BLOCKER_KIND = {"dependency", "permission", "question", "other"}


def report_problems(text: str) -> list[str]:
    """Hard problems of a report/2 sent back to baseline (by the VM bridge or the LOCAL executor)."""
    blocks = {k: v for k, v in BLOCK.findall(text)}
    if "ga" not in blocks:
        return ["no ```ga head block"]
    try:
        h = json.loads(blocks["ga"])
    except ValueError as e:
        return [f"head is not JSON: {e}"]
    out = []
    if h.get("schema") != "report/2":
        out.append("$.schema must be report/2")
    if not h.get("from"):
        out.append("$.from: is required (AGY = VM bridge, LOCAL = local executor)")
    hd = h.get("handled")
    if not isinstance(hd, list) or not hd:
        out.append("$.handled: is required (one entry per directive answered)")
    for i, x in enumerate(hd or []):
        if not (isinstance(x, dict) and ID_RE.match(str(x.get("id", ""))) and isinstance(x.get("rev_seen"), int)):
            out.append(f"$.handled[{i}]: needs id (CMD-<LETTERS><number>, the directive's id) and rev_seen (int)")
        elif x.get("status") not in REPORT_STATUS:
            out.append(f"$.handled[{i}].status must be done or declined (got {x.get('status')!r}); "
                       "a question goes in blockers with kind question")
    its = h.get("items")
    if not isinstance(its, list) or not its:
        out.append("$.items: is required (one per done_when id)")
    for i, x in enumerate(its or []):
        if not (isinstance(x, dict) and x.get("id") and x.get("state") in ITEM_STATE):
            out.append(f"$.items[{i}]: needs id (the done_when id, e.g. D1) and state met/unmet/na")
        elif x["state"] in ("met", "unmet") and not x.get("evidence"):
            out.append(f"$.items[{i}].evidence: required for met/unmet (commands run and what they printed)")
    for i, b in enumerate(h.get("blockers") or []):
        if not (isinstance(b, dict) and b.get("kind") in BLOCKER_KIND and b.get("what")):
            out.append(f"$.blockers[{i}]: needs kind ({'/'.join(sorted(BLOCKER_KIND))}) and what")
    return out


def check_mail(text: str) -> list[str]:
    hard, warn = problems(text)
    if hard:
        raise ValueError("; ".join(hard))
    return warn


def _mail(head: dict, spec: dict | None = None) -> str:
    t = "```ga\n" + json.dumps(head) + "\n```\n"
    return t + ("\n```ga-act\n" + json.dumps(spec) + "\n```\n" if spec else "")


def self_test() -> None:
    ok = {"schema": "directive/2", "id": "CMD-ACTB1", "rev": 1, "to": "AGY", "after": [], "goal": "g", "why": "w",
          "scope": [{"id": "S1", "text": "s"}], "done_when": [{"id": "D1", "text": "d"}], "model": "gemini-3.1-pro-high"}
    spec = {"item": {"id": "CMD-ACTB1", "goal": "g", "files": ["ga/bridge/act.py"]}, "base": "vm/G4-INT", "repo": "ga-sdk"}
    assert problems(_mail(ok, spec)) == ([], [])
    bad = {
        "rev 2 without changes (TKG13, ACTR1, ACTB1)": {**ok, "rev": 2},
        "no why (PING6)": {k: v for k, v in ok.items() if k != "why"},
        "dashed id (X0 10-07)": {**ok, "id": "CMD-G2-C1"},
        "old head (X0 10-06)": {**ok, "kind": "directive", "from": "baseline"},
        "wrong schema": {**ok, "schema": "directive/1"},
    }
    for name, h in bad.items():
        assert problems(_mail(h, {**spec, "item": {**spec["item"], "id": h["id"]}}))[0], name
    assert problems(_mail(ok, {**spec, "item": {**spec["item"], "files": []}}))[0], "empty files (GCK2)"
    good2 = {**ok, "rev": 2, "changes": [{"item": "D1", "op": "edit", "text": "t"}]}
    assert problems(_mail(good2, spec)) == ([], [])
    assert problems(_mail({**ok, "model": "gemini-9-ultra"}, spec))[1], "unknown model warns"
    print("mailcheck self-test OK")


def main(argv: list[str]) -> int:
    if argv[:1] == ["--report"]:
        rc = 0
        for p in argv[1:]:
            bad = report_problems(Path(p).read_text(encoding="utf-8"))
            if bad:
                rc = 1
                print(f"{p}: " + "; ".join(bad), file=sys.stderr)
            else:
                print(f"{p}: report/2 OK")
        return rc
    if argv == ["--self-test"]:
        self_test()
        return 0
    rc = 0
    for p in argv:
        hard, warn = problems(Path(p).read_text(encoding="utf-8"))
        for w in warn:
            print(f"{p}: warning: {w}", file=sys.stderr)
        if hard:
            rc = 1
            print(f"{p}: " + "; ".join(hard), file=sys.stderr)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
