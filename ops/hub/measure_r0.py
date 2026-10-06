"""OPS-R0 measurement (Ops): today's costs per session class and the shadow gate score, by code, no model.

    python3 ops/hub/measure_r0.py <list_sessions.json> <mailbox-ref> [out.json]
        list_sessions.json  raw list_sessions result ({"ccr":{"data":[...]}} or {"data":[...]})
        mailbox-ref         git ref of ga-mailbox (e.g. origin/ga-mailbox); shadow rows = to/baseline-shadow/*.md
        out                 default ops/flow/measure/R0.json

Session usage is cumulative per session; a rate is usage / (updated_at - created_at). Class rate = sum / sum of hours.
Shadow scoring follows ga/hub.py shadow_compare (by (id, rev), last shadow line wins, gate = last 10 all agree, 0 false
accepts) with one difference stated in the output: a baseline row carrying only `verdict: INTEGRATED` counts as ACCEPT.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
KST = timezone(timedelta(hours=9))
SAME = {"ACCEPT": "ACCEPT", "ACCEPTED": "ACCEPT", "CONTINUE": "ACCEPT", "INTEGRATED": "ACCEPT", "SEND_BACK": "SEND_BACK",
        "SENT_BACK": "SEND_BACK", "REFINE": "SEND_BACK", "ASK_HUMAN": "ASK_HUMAN", "ASK_USER": "ASK_HUMAN"}
GATE_N = 10
# The 62 ga-sdk environment failures (STATE.md GA54/GA56: "62 rlo-missing fails" = base, 1426 OK with rlo installed).
# Ops may not run ga-sdk code here; attribution is static: the test files that import rlo directly. The per-test list is
# DEV-R0c's acceptance (suite in the reference environment), re-measured by Ops on Dev's release/1.
ENV_FAILURES = {"count": 62, "cause": "rlo-sdk not installed in worker containers (pin in pyproject: rlo-sdk[sensor] @ rlo-SDK 0d92a3d)",
                "base": "ga-sdk 3d142ae (claude/CMD-GA49, integrated head)", "with_rlo": "1426 OK (hub preview verdict 21:00)",
                "test_files_importing_rlo": ["tests/test_ga28.py", "tests/test_ga29.py", "tests/test_ga31.py", "tests/test_gemini.py",
                                             "tests/test_pspec_prompts.py", "tests/test_rlo/test_gr3.py", "tests/test_rlo/test_gr4.py",
                                             "tests/test_rlo/test_gr9.py", "tests/test_rlo/test_no_shadow.py",
                                             "tests/test_rlo/test_units.py", "tests/test_wire.py"],
                "per_test_list": "owed by DEV-R0c run; not yet listed"}


def klass(s: dict) -> str:
    tags, t = " ".join(s.get("tags") or []), s.get("title") or ""
    if "integrator" in tags or "통합" in t:
        return "integrator"
    if "watcher" in tags or "감시" in t:
        return "watcher"
    if "baseline-hub" in tags or "허브" in t:
        return "hub"
    if "worker" in tags or "CMD-" in t:
        return "worker"
    return "other"


def ts(x: str) -> datetime:
    return datetime.fromisoformat(x.replace("Z", "+00:00"))


def sessions(raw: dict, day: str) -> dict:
    data = (raw.get("ccr") or raw)["data"]
    per, cls = [], {}
    for s in data:
        if not str(s.get("created_at", "")).startswith(day) and not str(s.get("updated_at", "")).startswith(day):
            continue
        u = (s.get("external_metadata") or {}).get("usage") or {}
        h = max((ts(s["updated_at"]) - ts(s["created_at"])).total_seconds() / 3600, 1 / 60)
        if klass(s) == "other":  # not part of the hub system (personal sessions)
            continue
        r = {"id": s["id"], "class": klass(s), "title": (s.get("title") or "")[:80], "hours": round(h, 2),
             "model": (s.get("external_metadata") or {}).get("last_served_model"),
             "input": u.get("input_tokens", 0), "output": u.get("output_tokens", 0), "cache_read": u.get("cache_read_tokens", 0),
             "cache_write": u.get("cache_write_tokens", 0), "usd": round(float(u.get("cost_usd", 0) or 0), 2)}
        per.append(r)
        c = cls.setdefault(r["class"], {"n": 0, "hours": 0.0, "input": 0, "output": 0, "cache_read": 0, "cache_write": 0, "usd": 0.0})
        for k in ("hours", "input", "output", "cache_read", "cache_write", "usd"):
            c[k] += r[k]
        c["n"] += 1
    for c in cls.values():
        h = c["hours"] or 1
        c["per_hour"] = {k: round(c[k] / h, 2 if k == "usd" else 0) for k in ("output", "cache_read", "cache_write", "usd")}
        c["hours"], c["usd"] = round(c["hours"], 2), round(c["usd"], 2)
    tot = sum(r["usd"] for r in per)
    span = (max(ts(s["updated_at"]) for s in data if s["id"] in {r["id"] for r in per})
            - min(ts(s["created_at"]) for s in data if s["id"] in {r["id"] for r in per})).total_seconds() / 3600 if per else 0
    return {"day_utc": day, "classes": cls, "total_usd": round(tot, 2), "wall_hours": round(span, 2),
            "usd_per_wall_hour": round(tot / span, 2) if span else None, "sessions": per}


def shadow_rows(ref: str) -> list[dict]:
    names = subprocess.run(["git", "ls-tree", "--name-only", ref, "to/baseline-shadow/"], capture_output=True, text=True, check=True).stdout.split()
    out = []
    for n in names:
        body = subprocess.run(["git", "show", f"{ref}:{n}"], capture_output=True, text=True, check=True).stdout
        m = re.search(r"```ga\s*\n(\{.*?\})\s*\n```", body, re.S)
        if m:
            sh = json.loads(m.group(1)).get("shadow") or {}
            out.append({**sh, "at": Path(n).name[:22]})
    return out


def score(baseline: list[dict], shadow: list[dict]) -> dict:
    norm = lambda d: SAME.get(str(d or "").strip().upper().replace("-", "_").replace(" ", "_"), str(d or "?"))  # noqa: E731
    key = lambda r: (str(r.get("id")), str(r.get("rev")))  # noqa: E731
    last = {key(r): r for r in shadow}
    rows, fa, extra, missing = [], [], [], []
    for b in baseline:
        k = key(b)
        if k not in last:
            missing.append(f"{k[0]} rev {k[1]}")
            continue
        bd, hd = norm(b.get("decision") or b.get("verdict")), norm(last[k].get("decision"))
        err = bool(last[k].get("error")) and hd == "ASK_HUMAN"
        rows.append({"id": k[0], "rev": k[1], "baseline": bd, "hub": hd, "agree": bd == hd and not err, "at": last[k]["at"]})
        if not err and hd == "ACCEPT" and bd == "SEND_BACK":
            fa.append(f"{k[0]} rev {k[1]}")
        if not err and hd == "SEND_BACK" and bd == "ACCEPT":
            extra.append(f"{k[0]} rev {k[1]}")
    rows.sort(key=lambda r: r["at"])
    run = 0
    for r in reversed(rows):
        if not r["agree"]:
            break
        run += 1
    return {"compared": len(rows), "agree": sum(r["agree"] for r in rows), "false_accepts": fa, "extra_send_backs": extra,
            "missing_in_shadow": missing, "gate": f"{min(run, GATE_N)}/{GATE_N}", "gate_ok": run >= GATE_N and not fa,
            "shadow_rows": len(shadow), "newest_shadow": max((r["at"] for r in shadow), default=None), "rows": rows}


def main(a: list[str]) -> int:
    raw = json.loads(Path(a[1]).read_text())
    now = datetime.now(KST)
    base = [json.loads(line) for line in (HERE / "baseline_verdicts.jsonl").read_text().splitlines() if line.strip()]
    out = {"schema": "ops-measure/1", "stage": "R0", "at": now.isoformat(timespec="seconds"),
           "cost": sessions(raw, datetime.now(timezone.utc).strftime("%Y-%m-%d")),
           "shadow_gate": score(base, shadow_rows(a[2])),
           "env_failures": ENV_FAILURES}
    p = Path(a[3]) if len(a) > 3 else HERE.parent / "flow" / "measure" / "R0.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
