"""Cloud session snapshot for GA Console (CMD-GA52): list_sessions JSON on stdin -> ops/hub/cloud_sessions.json.

Keeps only what the console shows (no transcript text, no tool lists). CMD-GA55 additions (optional fields, older
readers drop them): per-session token counts and parent id, and one account-wide `plan` block from rate_limit_info
(kind, status, reset time, overage flag; the API gives no usage percent, so none is invented). Written by the hub
(hourly routine and on events); the VM console reads it from the baseline integration branch.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))


def row(s: dict) -> dict:
    em = s.get("external_metadata") or {}
    pts = s.get("post_turn_summary") or em.get("post_turn_summary") or {}
    src = ((s.get("session_context") or {}).get("sources") or [{}])[0].get("git_repository") or {}
    u = em.get("usage") or {}
    return {
        "id": s.get("id"), "title": (s.get("title") or "")[:120],
        "status": str(s.get("session_status", "")).replace("SESSION_STATUS_", "").lower(),
        "bucket": str(s.get("status_bucket", "")).replace("SESSION_STATUS_BUCKET_", "").lower(),
        "detail": (pts.get("status_detail") or "")[:200],
        "repo": (src.get("url") or "").rsplit("/", 1)[-1], "branch": next(iter((em.get("current_branches") or {}).values()), None),
        "model": em.get("last_served_model") or (s.get("session_context") or {}).get("model"),
        "ctx": (em.get("context_usage") or {}).get("used_tokens"), "cost_usd": round(float(u.get("cost_usd", 0) or 0), 2),
        "tags": [t for t in s.get("tags") or [] if not t.startswith("config:")],
        "updated_at": s.get("updated_at"), "url": f"https://claude.ai/code/{s.get('id')}",
        "parent": s.get("parent_session_id"),
        "tokens": {k: int(u.get(k + "_tokens", 0) or 0) for k in ("input", "output", "cache_read", "cache_write")},
    }


def plan(sessions: list) -> dict | None:
    """Newest rate_limit_info across sessions (account-wide); None when no session carries one."""
    best = None
    for s in sessions:
        r = (s.get("external_metadata") or {}).get("rate_limit_info")
        if isinstance(r, dict) and (best is None or (s.get("updated_at") or "") > best[0]):
            best = (s.get("updated_at") or "", r)
    if best is None:
        return None
    r = best[1]
    reset = r.get("resetsAt")
    return {"kind": r.get("rateLimitType"), "status": r.get("status"), "overage": bool(r.get("isUsingOverage")),
            "resets_at": datetime.fromtimestamp(reset, KST).isoformat(timespec="minutes") if isinstance(reset, (int, float)) else None}


def main() -> int:
    raw = json.load(sys.stdin)
    d = raw.get("ccr", raw)
    data = [s for s in d.get("data", []) if str(s.get("id", "")).startswith("session_")]
    rows = [row(s) for s in data]
    out = {"schema": "cloud-sessions/1", "at": datetime.now(KST).isoformat(timespec="seconds"), "plan": plan(data), "sessions": rows}
    path = sys.argv[1] if len(sys.argv) > 1 else "ops/hub/cloud_sessions.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(f"{len(rows)} sessions -> {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
