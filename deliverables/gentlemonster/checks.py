"""Deterministic acceptance checks for the Gentle Monster application documents (BD-463).

Written by baseline; the executor may not edit it. Standard library only. Each job folder holds three files:
interpretation.md (the posting translated into the engine's directive form), application.md and portfolio.md.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HANGUL = re.compile(r"[가-힣]")
LATIN = re.compile(r"[A-Za-z]")
CONTACT = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+|01[0-9]-?\d{3,4}-?\d{4}|dbsurd")
FACT_MARKERS = ("GA Engine", "ga judge", "ga hub", "ga act", "라우터", "9,852", "2,530", "37,023", "llmsensor",
                "Chow", "analytical redundancy", "Telemetry", "Decision Context", "Policy Runtime", "GA Console", "Token",
                "agy", "Antigravity")
LIMITS = {"interpretation.md": (800, 6000), "application.md": (1500, 7000), "portfolio.md": (2000, 10000)}


def fail(msg):
    print("FAIL:", msg)
    sys.exit(1)


def body(job, name):
    p = HERE / job / name
    if not p.is_file():
        fail(f"{job}/{name} is missing")
    t = p.read_text(encoding="utf-8")
    lo, hi = LIMITS[name]
    if not lo <= len(t) <= hi:
        fail(f"{job}/{name}: {len(t)} characters, must be {lo}-{hi}")
    h, l = len(HANGUL.findall(t)), len(LATIN.findall(t))
    if h < 2 * l:
        fail(f"{job}/{name}: write in Korean (hangul {h} vs latin {l})")
    if CONTACT.search(t):
        fail(f"{job}/{name}: no real contact data; use [연락처] / [이메일]")
    return t


def headings(job, name, t, need):
    for h in need:
        if not re.search(r"^#{1,3} .*" + re.escape(h), t, re.M):
            fail(f"{job}/{name}: missing a heading with '{h}'")


def mentions(job, name, t, words):
    for w in words:
        if w not in t:
            fail(f"{job}/{name}: does not address '{w}'")


def facts_used(job, name, t, n):
    used = [m for m in FACT_MARKERS if m in t]
    if len(used) < n:
        fail(f"{job}/{name}: uses {len(used)} facts from source/facts.md ({used}); needs at least {n}")


def section(t, title):
    m = re.search(r"^#{1,3} [^\n]*" + re.escape(title) + r"[^\n]*\n(.*?)(?=^#{1,3} |\Z)", t, re.M | re.S)
    return m.group(1) if m else ""


def check(job, req_words, app_words, port_heads, port_words, gap_words):
    interp = body(job, "interpretation.md")
    headings(job, "interpretation.md", interp, ["goal", "scope", "done_when", "gap"])
    mentions(job, "interpretation.md", interp, req_words)
    app = body(job, "application.md")
    headings(job, "application.md", app, ["지원 동기", "직무 이해", "핵심 역량", "경험", "입사 후", "확인 필요"])
    mentions(job, "application.md", app, ["[이름]", "[연락처]"] + app_words)
    facts_used(job, "application.md", app, 4)
    todo = section(app, "확인 필요")
    for w in gap_words:
        if w not in todo:
            fail(f"{job}/application.md: the '확인 필요' section must list '{w}' (unknown, not invented)")
    port = body(job, "portfolio.md")
    headings(job, "portfolio.md", port, port_heads)
    mentions(job, "portfolio.md", port, port_words)
    facts_used(job, "portfolio.md", port, 5)
    print("ok", job)
