"""AO 토큰 분석: list_events 덤프 -> Claude Code JSONL 꼴 -> Telemetry from_cc_jsonl(L0) -> 집계.

L0 사건만 쓴다(llm.response 의 토큰 칸, tool.start/tool.end 의 글자 수, turn.start 의 origin).
'다시 읽힌 비용' = 도구 결과(또는 받은 입력)의 글자 수 x 그 뒤 압축 전까지의 모형 호출 수 -- 캐시 읽기 토큰의 원인 배분.
"""
import collections
import glob
import json
import sys

sys.path.insert(0, "/home/user/Telemetry")
from telemetry.collect import from_cc_jsonl  # noqa: E402

SRC = sys.argv[1:] or glob.glob("/tmp/claude-0/-home-user/d7b52199-cb2f-5033-a193-21ebbcd2a7a4/scratchpad/aoev/*")
AO_CLI = "a3964aa6-92e7-50e4-8d06-1ac61e6d7504"   # AO 의 CLI session_id
OUT = "/tmp/claude-0/-home-user/d7b52199-cb2f-5033-a193-21ebbcd2a7a4/scratchpad/ao_cc.jsonl"


def load(f):
    s = open(f).read()
    i, j = s.index('{"ccr"'), s.rindex("}") + 1
    return json.loads(s[i:j])["ccr"]["data"]


# 1. 덤프 -> 사건(uuid 로 중복 제거) -> 시각 순
seen, rows = set(), []
for f in SRC:
    for e in load(f):
        for k in ("assistant", "user", "result", "system"):
            if k not in e:
                continue
            body = e[k]
            uid = body.get("uuid")
            if uid in seen:
                continue
            seen.add(uid)
            c = body.get("internal_anthropic_catchall") or {}
            if c.get("session_id") not in (None, AO_CLI):
                continue                      # 다른 세션의 덤프
            rows.append((e.get("created_at"), k, uid, c))
rows.sort(key=lambda r: r[0] or "")

# 2. Claude Code JSONL 꼴로
with open(OUT, "w") as w:
    for at, k, uid, c in rows:
        line = {"type": k, "timestamp": at, "uuid": uid, "isSidechain": bool(c.get("parent_tool_use_id"))}
        if k in ("assistant", "user"):
            line["message"] = c.get("message")
            if k == "user":
                origin = c.get("origin") or {}
                if c.get("inbound_origin") == "mcp_send_message":
                    origin = {"kind": "cross-session"}
                line["origin"] = origin
                line["isMeta"] = c.get("isMeta")
                if c.get("isSynthetic") and isinstance((c.get("message") or {}).get("content"), str):
                    txt = c["message"]["content"]
                    if txt.startswith("This session is being continued"):
                        line["origin"] = {"kind": "compaction-summary"}
        elif k == "system":
            line.update({kk: c.get(kk) for kk in ("subtype", "compactMetadata") if kk in c})
        else:
            continue
        w.write(json.dumps(line, ensure_ascii=False) + "\n")

ev = from_cc_jsonl(OUT, "ao")

# 3. 집계
calls = [e for e in ev if e["type"] == "llm.response"]
tstart = {e["data"].get("tool_index"): e["data"] for e in ev if e["type"] == "tool.start"}
tools = collections.defaultdict(lambda: {"n": 0, "in": 0, "out": 0, "reread": 0})
turns = [e for e in ev if e["type"] == "turn.start"]
comp = [e for e in ev if e["type"] == "runtime.compaction"]


def g(e, k):
    return e["data"].get(k) or 0


tot = {k: sum(g(c, k) for c in calls) for k in ("input_tokens", "cache_read_input_tokens",
                                                   "cache_creation_input_tokens", "output_tokens")}
print("L0 events", len(ev), "| model calls", len(calls), "| turns", len(turns), "| compactions", len(comp))
print("tokens", tot, "| all", sum(tot.values()))
ctx = [g(c, "cache_read_input_tokens") + g(c, "cache_creation_input_tokens") + g(c, "input_tokens") for c in calls]
if ctx:
    print("context per call: mean %d  max %d  median %d" % (sum(ctx) / len(ctx), max(ctx), sorted(ctx)[len(ctx) // 2]))

# 호출 순번 -> 압축 경계(뒤 호출 수 계산용): 압축 직후 context 가 크게 줄어든 지점
bounds = [i for i in range(1, len(ctx)) if ctx[i] < ctx[i - 1] * 0.6]
print("compaction-like drops at call index", bounds, [(ctx[i - 1], ctx[i]) for i in bounds])


def calls_after(idx):
    nxt = [b for b in bounds if b > idx]
    end = nxt[0] if nxt else len(calls)
    return max(0, end - idx - 1)


for e in ev:
    if e["type"] == "tool.end":
        s = tstart.get(e["data"].get("tool_index")) or {}
        name = s.get("tool_name", "?")
        if name == "Bash":
            name = "Bash"
        t = tools[name]
        t["n"] += 1
        t["in"] += s.get("tool_input_chars") or 0
        out = e["data"].get("output_chars") or 0
        t["out"] += out
        t["reread"] += (out + (s.get("tool_input_chars") or 0)) * calls_after(s.get("call_index", 0))

print("\ntool                                   calls   input_ch  result_ch   re-read char-calls (= ch x later calls)")
for k, t in sorted(tools.items(), key=lambda kv: -kv[1]["reread"]):
    print("%-38s %5d %10d %10d %16d" % (k[:38], t["n"], t["in"], t["out"], t["reread"]))

# 차례(turn) 원천별: 그 차례가 낳은 모형 호출 수와 캐시 읽기
by = collections.defaultdict(lambda: {"turns": 0, "calls": 0, "cache_read": 0, "input_chars": 0, "reread": 0})
ci = 0
tlist = sorted(turns, key=lambda e: e["seq"])
cl = sorted(calls, key=lambda e: e["seq"])
for i, t in enumerate(tlist):
    nxt = tlist[i + 1]["seq"] if i + 1 < len(tlist) else 10 ** 12
    mine = [c for c in cl if t["seq"] < c["seq"] < nxt]
    o = t["data"].get("turn_origin") or "user"
    b = by[o]
    b["turns"] += 1
    b["calls"] += len(mine)
    b["cache_read"] += sum(g(c, "cache_read_input_tokens") for c in mine)
    b["input_chars"] += t["data"].get("input_chars") or 0
    if mine:
        idx = calls.index(mine[0])
        b["reread"] += (t["data"].get("input_chars") or 0) * (calls_after(idx) + 1)
print("\nturn origin            turns  model_calls  cache_read_tokens  input_chars  re-read char-calls")
for k, b in sorted(by.items(), key=lambda kv: -kv[1]["cache_read"]):
    print("%-22s %5d %12d %18d %12d %18d" % (k, b["turns"], b["calls"], b["cache_read"], b["input_chars"], b["reread"]))

json.dump(ev, open(OUT.replace(".jsonl", "_l0.json"), "w"), ensure_ascii=False)
