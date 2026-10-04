"""Sonnet / Haiku 로 GMG6 같은 한 턴 + pspec 계획 프롬프트(verbatim / compact). claude -p, 결과는 JSON 으로 남김."""
import json, subprocess, sys, os
from rlo import pspec as P
D = os.path.dirname(os.path.abspath(__file__))
spec = P.load_file("/home/user/baseline/ops/pspec/gemini-plan.pspec")
tools = {"read_file": {"about": "read a file from the workspace"},
         "search": {"about": "search the web; returns titles and urls"},
         "list_dir": {"about": "list a directory"},
         "write_note": {"about": "append a note to the user's notes"},
         "fetch_url": {"about": "fetch a url as text"},
         "noop": {}}
task = "Find the three most recent design notes about the hero banner and summarise what changed between them."
v = {"tools": tools, "task": task, "results": [], "ask": ""}
BARE = ["--tools", "", "--strict-mcp-config", "--no-session-persistence"]

def run(name, model, prompt, extra):
    cmd = ["claude", "-p", prompt, "--model", model, "--output-format", "json"] + extra
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=D)
    open(f"{D}/{name}.json", "w").write(r.stdout)
    d = json.loads(r.stdout)
    u = d["usage"]; mu = d.get("modelUsage") or {}
    row = {"case": name, "served": list(mu), "in": u["input_tokens"] + u["cache_read_input_tokens"] + u["cache_creation_input_tokens"],
           "out": u["output_tokens"], "usd": d.get("total_cost_usd"), "turns": d.get("num_turns"), "result": d["result"][:4000]}
    return row

rows = []
for m in sys.argv[1:]:
    if m != "haiku":
        rows.append(run(f"{m}_smoke", m, "Reply with the single word OK.", []))
    rows.append(run(f"{m}_smoke_bare", m, "Reply with the single word OK.", BARE + ["--system-prompt", "You are a helpful assistant."]))
    for mode in ("verbatim", "compact"):
        sysp = P.compile(spec, "once", v, mode); user = P.compile(spec, "first", v, mode)
        r = run(f"{m}_plan_{mode}", m, user, BARE + ["--system-prompt", sysp])
        r["prompt_est_tokens"] = P.tokens(sysp) + P.tokens(user)
        r["check"] = P.check_text(spec, r["result"], {"tools": tools})
        rows.append(r)
json.dump(rows, open(f"{D}/rows_{'_'.join(sys.argv[1:])}.json", "w"), indent=1)
for r in rows:
    print(json.dumps({k: r[k] for k in r if k != "result"}))
