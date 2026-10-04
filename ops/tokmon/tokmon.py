"""토큰 감시(BD-305): 세션 사용량 읽기를 지난 스냅숏과 비교해 경보만 낸다.

입력(stdin): get_session 결과 JSON 을 한 줄에 하나씩(여러 줄). 세션 id · 제목 · context_usage.used_tokens ·
usage(cache_read_tokens, cache_write_tokens, output_tokens, cost_usd)만 쓴다. 메시지 본문은 읽지 않는다.
출력: 경보 줄(없으면 아무것도 안 찍음). 스냅숏은 --state 파일에 쓴다(다음 비교의 기준).

경보: ctx      문맥 > --ctx-max (기본 150000)
      burst    지난 스냅숏 뒤 캐시 읽기 증가 > --read-max (기본 20000000)
      growth   지난 스냅숏 뒤 문맥 증가 > --ctx-grow (기본 50000)
"""
from __future__ import annotations

import argparse
import json
import sys
import time


def reading(d: dict) -> "dict | None":
    s = d.get("ccr", d)
    em = s.get("external_metadata") or {}
    u = em.get("usage") or {}
    if not str(s.get("id", "")).startswith("session_"):
        return None
    return {"id": s["id"], "title": (s.get("title") or "")[:40], "status": s.get("session_status", ""),
            "ctx": (em.get("context_usage") or {}).get("used_tokens"),
            "cache_read": u.get("cache_read_tokens", 0), "cache_write": u.get("cache_write_tokens", 0),
            "output": u.get("output_tokens", 0), "usd": round(u.get("cost_usd", 0.0), 2)}


def alarms(prev: dict, cur: dict, *, ctx_max: int, read_max: int, ctx_grow: int) -> list[str]:
    out = []
    c = cur.get("ctx")
    if c is not None and c > ctx_max:
        out.append(f"ctx {cur['id']} {cur['title']}: context {c} > {ctx_max}")
    if prev:
        dr = cur["cache_read"] - prev.get("cache_read", 0)
        if dr > read_max:
            out.append(f"burst {cur['id']} {cur['title']}: cache_read +{dr} since last snapshot")
        if c is not None and prev.get("ctx") is not None and c - prev["ctx"] > ctx_grow:
            out.append(f"growth {cur['id']} {cur['title']}: context +{c - prev['ctx']} since last snapshot")
    return out


def main(argv=None) -> int:
    a = argparse.ArgumentParser()
    a.add_argument("--state", required=True)
    a.add_argument("--ctx-max", type=int, default=150000)
    a.add_argument("--read-max", type=int, default=20000000)
    a.add_argument("--ctx-grow", type=int, default=50000)
    o = a.parse_args(argv)
    try:
        snap = json.load(open(o.state))
    except (OSError, ValueError):
        snap = {"t": None, "sessions": {}}
    new = {}
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        r = reading(json.loads(line))
        if r:
            new[r["id"]] = r
            for x in alarms(snap["sessions"].get(r["id"], {}), r, ctx_max=o.ctx_max, read_max=o.read_max,
                            ctx_grow=o.ctx_grow):
                print(x)
    snap = {"t": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "sessions": {**snap["sessions"], **new}}
    json.dump(snap, open(o.state, "w"), indent=1, sort_keys=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
