"""Hourly per-class measurement (OPS-VMAUTO, OPS-BASEAUTO): current burn, not lifetime averages. Code only, no model.

    python3 ops/hub/measure_hourly.py tick <list_sessions.json>     -> one row: per-class delta since the last tick
    python3 ops/hub/measure_hourly.py handoff <role> <old> <new> <crossed_at> <ack_at> [lost] [dup]
    python3 ops/hub/measure_hourly.py --self-test

A tick compares each session's cumulative usage with the previous tick (ops/flow/measure/last.json) and divides by the
elapsed wall time, so idle and archived sessions add 0 (the lifetime-average watcher metric counted them; WATCH-METRIC).
Classes: baseline (top hub, assign.json baseline.hub), dev_hub, ops_hub (assign.json), integrator, worker, watcher,
vm_auto (rows Ops adds from VM status/1 once DEV-VMAUTO reports usage). Units as ops/flow/measure/R0.json per_hour.
Rows go to ops/flow/measure/hourly.jsonl (last KEEP rows), handoffs to handoffs.jsonl.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
MEAS = HERE.parent / "flow" / "measure"
ASSIGN = HERE.parent / "flow" / "assign.json"
KEEP = 72
FIELDS = ("input", "output", "cache_read", "cache_write", "usd")


def ts(x: str) -> datetime:
    return datetime.fromisoformat(x.replace("Z", "+00:00"))


def klass(s: dict, assign: dict) -> str:
    sid, tags, t = s.get("id"), " ".join(s.get("tags") or []), s.get("title") or ""
    for role in ("baseline", "dev", "ops"):
        if sid == (assign.get(role) or {}).get("hub"):
            return "baseline" if role == "baseline" else f"{role}_hub"
    if "integrator" in tags or "통합" in t:
        return "integrator"
    if "watcher" in tags or "감시" in t:
        return "watcher"
    if "baseline-hub" in tags or "허브" in t:
        return "hub_other"
    if "worker" in tags or "CMD-" in t:
        return "worker"
    return "other"


def usage(s: dict) -> dict:
    em = s.get("external_metadata") or {}
    u = em.get("usage") or {}
    return {"input": u.get("input_tokens", 0), "output": u.get("output_tokens", 0), "cache_read": u.get("cache_read_tokens", 0),
            "cache_write": u.get("cache_write_tokens", 0), "usd": float(u.get("cost_usd", 0) or 0),
            "ctx": (em.get("context_usage") or {}).get("used_tokens")}


def tick(raw: dict, last: dict, assign: dict, now: datetime) -> tuple[dict, dict]:
    data = (raw.get("ccr") or raw).get("data") or []
    prev_at = ts(last["at"]) if last.get("at") else None
    hours = (now - prev_at).total_seconds() / 3600 if prev_at else None
    cur, cls = {}, {}
    for s in data:
        k = klass(s, assign)
        if k == "other":
            continue
        u = usage(s)
        cur[s["id"]] = {f: u[f] for f in FIELDS}
        p = (last.get("sessions") or {}).get(s["id"])
        d = {f: max(u[f] - p[f], 0) for f in FIELDS} if p else None  # new session: baseline only, counted next tick
        c = cls.setdefault(k, {"n": 0, "active": 0, **{f: 0 for f in FIELDS}, "ctx_max": 0})
        c["n"] += 1
        if u["ctx"] and "ARCHIVED" not in str(s.get("session_status") or s.get("status") or ""):
            c["ctx_max"] = max(c["ctx_max"], u["ctx"])
        if d and any(d.values()):
            c["active"] += 1
            for f in FIELDS:
                c[f] += d[f]
    for c in cls.values():
        c["usd"] = round(c["usd"], 2)
        c["per_hour"] = {f: round(c[f] / hours, 2 if f == "usd" else 0) for f in ("output", "cache_read", "cache_write", "usd")} \
            if hours else None
    row = {"schema": "ops-measure-hourly/1", "at": now.isoformat(timespec="seconds"), "hours": round(hours, 2) if hours else None,
           "classes": cls, "total_usd_per_h": round(sum(c["usd"] for c in cls.values()) / hours, 2) if hours else None}
    return row, {"at": row["at"], "sessions": cur}


def append(path: Path, row: dict, keep: int | None = None) -> None:
    lines = path.read_text().splitlines() if path.exists() else []
    lines.append(json.dumps(row, ensure_ascii=False))
    path.write_text("\n".join(lines[-keep:] if keep else lines) + "\n")


def handoff(a: list[str]) -> dict:
    role, old, new, crossed, ack = a[:5]
    lost, dup = (int(a[5]) if len(a) > 5 else 0), (int(a[6]) if len(a) > 6 else 0)
    return {"schema": "ops-handoff/1", "role": role, "old": old, "new": new, "crossed_at": crossed, "ack_at": ack,
            "latency_min": round((ts(ack) - ts(crossed)).total_seconds() / 60, 1), "lost": lost, "dup": dup}


def self_test() -> None:
    assign = {"baseline": {"hub": "B"}, "dev": {"hub": "D"}, "ops": {"hub": "O"}}
    def s(i, usd, cr, title="", tags=(), st="RUNNING"):
        return {"id": i, "title": title, "tags": list(tags), "session_status": st,
                "external_metadata": {"usage": {"cost_usd": usd, "cache_read_tokens": cr, "output_tokens": 10},
                                      "context_usage": {"used_tokens": 1000}}}
    t0, t1 = datetime(2026, 10, 7, 0, tzinfo=timezone.utc), datetime(2026, 10, 7, 2, tzinfo=timezone.utc)
    r0, st0 = tick({"data": [s("B", 10, 100), s("W", 5, 50, tags=["baseline-worker"]), s("X", 99, 0, st="ARCHIVED", title="CMD-1")]},
                   {}, assign, t0)
    assert r0["hours"] is None and r0["total_usd_per_h"] is None
    r1, _ = tick({"data": [s("B", 14, 300), s("W", 5, 50, tags=["baseline-worker"]), s("X", 99, 0, st="ARCHIVED", title="CMD-1")]},
                 st0, assign, t1)
    assert r1["classes"]["baseline"]["per_hour"]["usd"] == 2.0, r1
    assert r1["classes"]["worker"]["usd"] == 0 and r1["classes"]["worker"]["active"] == 0  # idle + archived add 0
    assert r1["total_usd_per_h"] == 2.0
    h = handoff(["dev", "a", "b", "2026-10-06T23:50:00+09:00", "2026-10-06T23:58:30+09:00"])
    assert h["latency_min"] == 8.5 and h["lost"] == 0
    print("ok")


def main(a: list[str]) -> int:
    if a[:1] == ["--self-test"]:
        self_test()
        return 0
    MEAS.mkdir(parents=True, exist_ok=True)
    if a[:1] == ["tick"] and len(a) == 2:
        lastf = MEAS / "last.json"
        last = json.loads(lastf.read_text()) if lastf.exists() else {}
        row, state = tick(json.loads(Path(a[1]).read_text()), last, json.loads(ASSIGN.read_text()), datetime.now(timezone.utc))
        vb = MEAS / "VM_BASELINE.json"  # OPS-R0FREEZE: every row names the code it ran on
        row["vm_baseline"] = json.loads(vb.read_text()) if vb.exists() else None
        lastf.write_text(json.dumps(state) + "\n")
        if row["hours"]:
            append(MEAS / "hourly.jsonl", row, KEEP)
        print(json.dumps(row, ensure_ascii=False))
        return 0
    if a[:1] == ["handoff"] and len(a) >= 6:
        row = handoff(a[1:])
        append(MEAS / "handoffs.jsonl", row)
        print(json.dumps(row))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
