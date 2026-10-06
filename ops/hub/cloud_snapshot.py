"""Cloud session snapshot for GA Console (CMD-GA52): list_sessions JSON on stdin -> ops/hub/cloud_sessions.json.

Keeps only what the console shows (no transcript text, no tool lists, no rate-limit data). Written by the hub
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
    }


def main() -> int:
    raw = json.load(sys.stdin)
    d = raw.get("ccr", raw)
    rows = [row(s) for s in d.get("data", []) if str(s.get("id", "")).startswith("session_")]
    out = {"schema": "cloud-sessions/1", "at": datetime.now(KST).isoformat(timespec="seconds"), "sessions": rows}
    path = sys.argv[1] if len(sys.argv) > 1 else "ops/hub/cloud_sessions.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(f"{len(rows)} sessions -> {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
