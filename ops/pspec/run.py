import sys, json, itertools
import os; sys.path.insert(0, os.environ.get("GA_SDK", "../../../ga-sdk")); sys.path.insert(0, os.path.dirname(__file__))
import pspec as P
from ga import gemini as G
from pathlib import Path

spec = P.load(open(os.path.join(os.path.dirname(__file__), "gemini-plan.pspec")).read())
tools = {"read_file": {"about": "read a file from the workspace"},
         "search": {"about": "search the web; returns titles and urls"},
         "list_dir": {"about": "list a directory"},
         "write_note": {"about": "append a note to the user's notes"},
         "fetch_url": {"about": "fetch a url as text"},
         "noop": {}}
cfg = G.GeminiConfig(root=Path("."), tools=tools)
task = "Find the three most recent design notes about the hero banner and summarise what changed between them."

# 1. verbatim == today's text
ok = True
for tl in (tools, {}, {"x": {"about": ""}}):
    c = G.GeminiConfig(root=Path("."), tools=tl)
    want = G.protocol(c)
    got = P.compile(spec, "once", {"tools": tl, "task": "", "results": [], "ask": ""})
    ok &= (want == got)
    want_f = G.protocol(c) + "\nTask:\n" + task
    ok &= want_f == P.compile(spec, "first", {"tools": tl, "task": task, "results": [], "ask": ""})
print("verbatim once/first byte-identical:", ok)

res = [{"id": "a", "tool": "search", "text": "3 hits: notes/hero-v1.md, notes/hero-v2.md, notes/hero-v3.md"},
       {"id": "b", "tool": "list_dir", "text": "notes/: hero-v1.md hero-v2.md hero-v3.md footer.md"}]
ask = "read the three hero notes and compare them"
want_t = "\n".join([f"Reply with one {G.PLAN_SCHEMA} JSON object, as before.", "Results:"] + [f"- {r['id']} ({r['tool']}): {r['text']}" for r in res] + ["", "Your next step: " + ask])
got_t = P.compile(spec, "turn", {"tools": tools, "task": task, "results": res, "ask": ask})
want_n = "\n".join([G.protocol(cfg), "Task:", task, "", "Results:"] + [f"- {r['id']} ({r['tool']}): {r['text']}" for r in res] + ["", "Your next step: " + ask])
got_n = P.compile(spec, "turn_noresume", {"tools": tools, "task": task, "results": res, "ask": ask})
print("verbatim turn / turn_noresume byte-identical:", want_t == got_t, want_n == got_n)

# 2. checker agrees with ga's check_plan on accept/reject
plans = [
 {"schema": "ga-gemini-plan/1", "steps": [{"id": "a", "tool": "search", "args": {"q": "x"}}], "next": {"prompt": "go", "after": ["a"]}, "say": "hi"},
 {"schema": "ga-gemini-plan/1", "steps": [], "next": None},
 {"schema": "ga-gemini-plan/1", "steps": [{"id": "a", "tool": "nope"}]},
 {"schema": "ga-gemini-plan/2", "steps": []},
 {"schema": "ga-gemini-plan/1", "steps": [{"id": "a", "tool": "search", "after": ["b"]}]},
 {"schema": "ga-gemini-plan/1", "steps": [{"id": "a", "tool": "search"}, {"id": "a", "tool": "noop"}]},
 {"schema": "ga-gemini-plan/1", "steps": [{"id": "this-id-is-too-long", "tool": "noop"}]},
 {"schema": "ga-gemini-plan/1", "steps": [{"id": "a", "tool": "noop", "args": []}]},
 {"schema": "ga-gemini-plan/1", "next": {"prompt": "  "}},
 {"schema": "ga-gemini-plan/1", "next": {"prompt": "x", "after": ["z"]}},
 {"schema": "ga-gemini-plan/1", "extra": 1},
 {"schema": "ga-gemini-plan/1", "say": 3},
 {"schema": "ga-gemini-plan/1", "steps": [{"id": "s%d" % i, "tool": "noop"} for i in range(17)]},
 {"schema": "ga-gemini-plan/1", "steps": [{"id": "s%d" % i, "tool": "noop"} for i in range(16)]},
 {"schema": "ga-gemini-plan/1", "steps": [{"id": "a", "tool": "noop", "zz": 1}]},
 "not an object",
]
agree = [bool(G.check_plan(p, tools)) == bool(P.check(spec, p, {"tools": tools})) for p in plans]
print("checker agrees with ga check_plan:", sum(agree), "/", len(agree), [i for i, a in enumerate(agree) if not a])

# 3. tokens: an 8-turn conversation
turns = [res[: (i % 2) + 1] for i in range(7)]
def conv(mode, resume):
    t = [P.tokens(P.compile(spec, "first", {"tools": tools, "task": task, "results": [], "ask": ""}, mode))]
    for r in turns:
        sec = "turn" if resume else "turn_noresume"
        t.append(P.tokens(P.compile(spec, sec, {"tools": tools, "task": task, "results": r, "ask": ask}, mode)))
    return t
for resume in (True, False):
    v, c = conv("verbatim", resume), conv("compact", resume)
    print(f"{'resume host (gemini)' if resume else 'no-resume host (agy)':24s} verbatim {sum(v):5d}  compact {sum(c):5d}  saved {100*(1-sum(c)/sum(v)):.0f}%   first turn {v[0]} -> {c[0]}")
print()
print(P.compile(spec, "first", {"tools": tools, "task": task, "results": [], "ask": ""}, "compact"))
print("---"); print(P.compile(spec, "turn", {"tools": tools, "task": task, "results": res, "ask": ask}, "compact"))
