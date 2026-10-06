"""OPS-SH1 (Ops): collect shadow rows (ga-engine internal rejections) and send baseline ONE batched shadow/1 digest.

Rows come from Dev, Ops and the VM engine. Each row is checked as a shadow/1 by ops/flow/flow.py when it is staged
(rejected_by must be a ga-engine source; a platform permission denial is never a row). Staged rows wait in
ops/flow/shadow/pending/; `digest` sends them as one shadow/1 (rows inside) when the oldest is >= PERIOD old or a row
says it blocks a dependent chain, then moves them to ops/flow/shadow/sent/<digest id>/. Routine successes never come
here: they stay on the dashboard.

    python3 ops/hub/shadow_digest.py stage <dev|ops|vm> <row.json>   row = {id, action, rejected_by, reason, would_do,
                                                                      evidence?, blocks_chain?: bool}
    python3 ops/hub/shadow_digest.py digest [--force]               -> path of the shadow/1 sent, or nothing
    python3 ops/hub/shadow_digest.py --self-test
"""
from __future__ import annotations

import collections
import json
import shutil
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "flow"))
import flow  # noqa: E402

KST = timezone(timedelta(hours=9))
PERIOD = timedelta(minutes=60)
ACTORS = {"dev", "ops", "vm"}


def _dirs(root: Path) -> tuple[Path, Path]:
    return root / "shadow" / "pending", root / "shadow" / "sent"


def stage(actor: str, row: dict, root: Path = flow.HERE) -> Path:
    if actor not in ACTORS:
        raise flow.FlowError(f"actor must be one of {sorted(ACTORS)}")
    row = {**row, "actor": actor}
    flow.check("dev" if actor == "dev" else "ops", "baseline", "shadow/1", row)  # vm rows are relayed by Ops
    now = datetime.now(KST)
    pend, _ = _dirs(root)
    pend.mkdir(parents=True, exist_ok=True)
    p = pend / f"{now:%Y%m%dT%H%M%S}-{actor}-{row['id']}.json"
    p.write_text(json.dumps({**row, "staged_at": now.isoformat(timespec="seconds")}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return p


def digest(force: bool = False, root: Path = flow.HERE, now: datetime | None = None) -> Path | None:
    pend, sent = _dirs(root)
    files = sorted(pend.glob("*.json")) if pend.is_dir() else []
    if not files:
        return None
    rows = [json.loads(f.read_text()) for f in files]
    now = now or datetime.now(KST)
    oldest = min(datetime.fromisoformat(r["staged_at"]) for r in rows)
    blocked = [r["id"] for r in rows if r.get("blocks_chain")]
    if not (force or blocked or now - oldest >= PERIOD):
        return None
    by = collections.Counter(r["rejected_by"] for r in rows)
    did = f"SHD-{now:%Y%m%dT%H%M}"
    msg = {"id": did, "actor": "ops", "action": f"digest of {len(rows)} rejected engine action(s)",
           "rejected_by": by.most_common(1)[0][0], "reason": ", ".join(f"{k} {v}" for k, v in sorted(by.items())),
           "would_do": "; ".join(f"{r['actor']}:{r['id']} {r['would_do']}" for r in rows)[:1000],
           "evidence": {"period_from": oldest.isoformat(timespec="seconds"), "blocked_chain": blocked,
                        "rows": [{k: r.get(k) for k in ("id", "actor", "action", "rejected_by", "reason", "would_do", "evidence", "blocks_chain")}
                                 for r in rows]}}
    p = flow.send("ops", "baseline", "shadow/1", msg, root)
    dest = sent / did
    dest.mkdir(parents=True, exist_ok=True)
    for f in files:
        shutil.move(str(f), dest / f.name)
    return p


def _self_test() -> None:
    r = Path(tempfile.mkdtemp())
    row = {"id": "R1", "action": "push", "rejected_by": "budget", "reason": "day cap", "would_do": "push x"}
    stage("vm", row, r)
    assert digest(root=r) is None  # younger than PERIOD, nothing blocked
    try:
        stage("dev", {**row, "rejected_by": "platform"}, r)
        raise AssertionError("platform denial staged")
    except flow.FlowError:
        pass
    stage("dev", {**row, "id": "R2", "rejected_by": "guard", "blocks_chain": True}, r)
    p = digest(root=r)
    m = json.loads(p.read_text())
    assert m["form"] == "shadow/1" and len(m["evidence"]["rows"]) == 2 and m["evidence"]["blocked_chain"] == ["R2"]
    assert digest(root=r) is None and not list((r / "shadow" / "pending").glob("*.json"))
    stage("ops", {**row, "id": "R3"}, r)
    assert digest(root=r, now=datetime.now(KST) + PERIOD) is not None
    print("self-test ok")


def main(a: list[str]) -> int:
    try:
        if a[1:2] == ["--self-test"]:
            _self_test()
        elif a[1:2] == ["stage"] and len(a) == 4:
            print(stage(a[2], json.loads(Path(a[3]).read_text(encoding="utf-8"))))
        elif a[1:2] == ["digest"]:
            p = digest(force="--force" in a)
            if p:
                print(p)
        else:
            print(__doc__)
            return 1
    except flow.FlowError as e:
        print(f"REJECTED: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
