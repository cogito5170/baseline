"""One mailbox tick for the direct pipeline (policy direct_pipeline_1007, user 10-08 06:0x KST: "너도 자동으로 메일함
확인해서 교신해 ... semantic 포맷은 그대로 ... 토큰 최적화 ... 세션을 갈아줘 ... 사용 토큰량을 계산해").

Code only, no model: everything a tick can decide by rule is done here, so the routine session that runs it spends
tokens only on what needs judgement (an unmet directive, a format problem, a user decision).

    python3 ops/flow/mailbox_tick.py tick <mailbox worktree>        -> JSON summary on stdout
    python3 ops/flow/mailbox_tick.py claude-usage <get_session.json> <run label>
    python3 ops/flow/mailbox_tick.py report                          -> token totals per side, per model
    python3 ops/flow/mailbox_tick.py --self-test

tick:
  1. pull the mailbox (branch ga-mailbox) in the given worktree
  2. every new to/baseline/*-LOCAL-*.md: check report/2 (mailcheck.report_problems); record the outcome of each handled
     directive (met = every item met) and the VM token numbers from its results into measure/tokens.jsonl
  3. send queued directives (ops/flow/queue.json) whose `after_met` are all met and that do not need the user; mails are
     built by mailform (directive/2, to LOCAL) and pushed in one commit
  4. print what needs judgement: unmet / declined / invalid reports, queue items waiting for the user
State: ops/flow/measure/tick_state.json (seen reports, outcomes, sent ids). Ledger: ops/flow/measure/tokens.jsonl.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import mailcheck  # noqa: E402
import mailform  # noqa: E402

STATE = HERE / "measure" / "tick_state.json"
LEDGER = HERE / "measure" / "tokens.jsonl"
QUEUE = HERE / "queue.json"
REPORT = re.compile(r"-LOCAL-(CMD-[A-Z]+\d+|[\w-]+)\.md$")
NUM_KEYS = ("input_tokens", "output_tokens", "cached_tokens", "tokens", "turns", "seconds")


def now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def load(p: Path, default):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def save(p: Path, v) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(v, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def append(row: dict) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def git(box: Path, *a: str, check: bool = True) -> str:
    p = subprocess.run(["git", "-C", str(box), *a], capture_output=True, text=True)
    if check and p.returncode:
        raise SystemExit(f"git {' '.join(a[:2])}: {(p.stderr or p.stdout).strip()[:300]}")
    return p.stdout


def head_of(text: str) -> dict:
    m = mailcheck.BLOCK.search(text)
    return json.loads(m.group(2)) if m and m.group(1) == "ga" else {}


def vm_row(name: str, head: dict) -> dict:
    res = {r.get("name"): r.get("value") for r in head.get("results") or [] if isinstance(r, dict)}
    row = {"schema": "tokens/1", "at": now(), "side": "vm", "mail": name,
           "ids": [h.get("id") for h in head.get("handled") or []], "model": res.get("model")}
    for k in NUM_KEYS:
        v = res.get(k)
        row[k] = v if isinstance(v, (int, float)) else None
    return row


def outcome(head: dict, hid: str) -> str:
    h = next((x for x in head.get("handled") or [] if x.get("id") == hid), {})
    if h.get("status") == "declined":
        return "declined"
    states = [i.get("state") for i in head.get("items") or []]
    return "met" if states and all(s in ("met", "na") for s in states) else "unmet"


def tick(box: Path) -> dict:
    st = load(STATE, {"seen": [], "outcomes": {}, "sent": []})
    git(box, "pull", "-q", "--rebase", "origin", "ga-mailbox")
    out = {"at": now(), "new_reports": [], "needs_judgement": [], "sent": [], "waiting_user": [], "other_mail": 0}
    for f in sorted((box / "to" / "baseline").glob("*.md")):
        if f.name in st["seen"]:
            continue
        st["seen"].append(f.name)
        if not REPORT.search(f.name):
            out["other_mail"] += 1
            continue
        text = f.read_text(encoding="utf-8")
        bad = mailcheck.report_problems(text)
        head = head_of(text) if not bad or "head is not JSON" not in bad[0] else {}
        if head.get("results"):
            append(vm_row(f.name, head))
        if bad:
            out["needs_judgement"].append({"mail": f.name, "why": "format", "problems": bad})
            continue
        for h in head["handled"]:
            o = outcome(head, h["id"])
            st["outcomes"][h["id"]] = {"state": o, "rev": h.get("rev_seen"), "mail": f.name}
            out["new_reports"].append({"id": h["id"], "outcome": o, "mail": f.name})
            if o != "met":
                out["needs_judgement"].append({"mail": f.name, "id": h["id"], "why": o,
                                               "items": [i for i in head["items"] if i.get("state") != "met"]})
    queue = load(QUEUE, [])
    wrote = []
    for q in queue:
        qid = q["info"]["id"]
        if qid in st["sent"]:
            continue
        deps = q.get("after_met") or []
        if not all((st["outcomes"].get(d) or {}).get("state") == "met" for d in deps):
            continue
        if q.get("needs_user"):
            out["waiting_user"].append({"id": qid, "what": q.get("what") or q["info"].get("title")})
            continue
        text, head, notes = mailform.build(q["info"])
        wrote.append(mailform.write(box, text, head))
        st["sent"].append(qid)
        out["sent"].append({"id": qid, "notes": notes})
    if wrote:
        git(box, "add", *[str(p.relative_to(box)) for p in wrote])
        git(box, "commit", "-q", "-m", "ga mail: baseline -> LOCAL " + ", ".join(s["id"] for s in out["sent"]) + " (tick)")
        for _ in range(3):
            if subprocess.run(["git", "-C", str(box), "push", "-q", "origin", "HEAD:ga-mailbox"]).returncode == 0:
                break
            git(box, "pull", "-q", "--rebase", "origin", "ga-mailbox")
    save(STATE, st)
    return out


def claude_usage(path: str, label: str) -> dict:
    s = load(Path(path), {})
    s = s.get("ccr", s)
    em = s.get("external_metadata") or {}
    u = em.get("usage") or {}
    row = {"schema": "tokens/1", "at": now(), "side": "claude", "run": label, "session": s.get("id"),
           "model": em.get("last_served_model") or (s.get("session_context") or {}).get("model"),
           "input_tokens": u.get("input_tokens"), "output_tokens": u.get("output_tokens"),
           "cached_tokens": u.get("cache_read_tokens"), "cache_write_tokens": u.get("cache_write_tokens", u.get("cache_creation_tokens")),
           "usd": u.get("cost_usd"), "context": (em.get("context_usage") or {}).get("used_tokens")}
    append(row)
    return row


def report() -> dict:
    tot: dict = {}
    for line in LEDGER.read_text(encoding="utf-8").splitlines() if LEDGER.exists() else []:
        r = json.loads(line)
        k = f"{r['side']}:{r.get('model') or '?'}"
        t = tot.setdefault(k, {"rows": 0})
        t["rows"] += 1
        for f in ("input_tokens", "output_tokens", "cached_tokens", "tokens", "usd"):
            if isinstance(r.get(f), (int, float)):
                t[f] = round(t.get(f, 0) + r[f], 4)
    return tot


def self_test() -> None:
    global STATE, LEDGER, QUEUE
    import tempfile
    d = Path(tempfile.mkdtemp())
    STATE, LEDGER, QUEUE = d / "s.json", d / "t.jsonl", d / "q.json"
    sh = lambda *a, cwd=None: subprocess.run(a, cwd=cwd, check=True, capture_output=True)  # noqa: E731
    sh("git", "init", "-q", "--bare", "-b", "ga-mailbox", str(d / "o.git"))
    sh("git", "clone", "-q", str(d / "o.git"), str(d / "box"))
    box = d / "box"
    sh("git", "checkout", "-q", "-b", "ga-mailbox", cwd=box)
    rep = {"schema": "report/2", "from": "LOCAL", "handled": [{"id": "CMD-LOC3", "rev_seen": 1, "status": "done"}],
           "items": [{"id": "D1", "state": "met", "evidence": ["ok"]}],
           "results": [{"name": "model", "value": "gemini-3.1-pro-high"}, {"name": "input_tokens", "value": 900},
                       {"name": "output_tokens", "value": 100}, {"name": "cached_tokens", "value": 600}]}
    (box / "to" / "baseline").mkdir(parents=True)
    (box / "to" / "baseline" / "20261008T000000Z-LOCAL-CMD-LOC3.md").write_text("```ga\n" + json.dumps(rep) + "\n```\n")
    (box / "to" / "baseline" / "20261008T000001Z-AGY-x.md").write_text("x")
    sh("git", "add", ".", cwd=box)
    sh("git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "r", cwd=box)
    sh("git", "push", "-q", "origin", "ga-mailbox", cwd=box)
    save(QUEUE, [{"info": {"id": "CMD-LOC9", "title": "t", "goal": "g", "why": "w", "read_only": True}, "after_met": ["CMD-LOC3"]},
                 {"info": {"id": "CMD-LOC8", "title": "deploy", "goal": "g", "why": "w", "read_only": True},
                  "after_met": ["CMD-LOC3"], "needs_user": True}])
    o = tick(box)
    assert o["new_reports"] == [{"id": "CMD-LOC3", "outcome": "met", "mail": "20261008T000000Z-LOCAL-CMD-LOC3.md"}], o
    assert [s["id"] for s in o["sent"]] == ["CMD-LOC9"] and o["waiting_user"][0]["id"] == "CMD-LOC8" and o["other_mail"] == 1
    assert list((box / "to" / "LOCAL").glob("*CMD-LOC9.md"))
    o2 = tick(box)
    assert not o2["new_reports"] and not o2["sent"], o2
    t = report()
    assert t["vm:gemini-3.1-pro-high"]["cached_tokens"] == 600, t
    print("mailbox_tick self-test OK")


def main(a: list[str]) -> int:
    if a == ["--self-test"]:
        self_test()
    elif a[:1] == ["tick"] and len(a) == 2:
        print(json.dumps(tick(Path(a[1])), ensure_ascii=False, indent=1))
    elif a[:1] == ["claude-usage"] and len(a) == 3:
        print(json.dumps(claude_usage(a[1], a[2]), ensure_ascii=False))
    elif a == ["report"]:
        print(json.dumps(report(), ensure_ascii=False, indent=1))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
