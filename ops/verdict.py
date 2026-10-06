"""One-call verdict for a ga-sdk worker branch (BD-464: fewer baseline tool calls per verdict).

    python3 ops/verdict.py <branch> [--mut mutations.json] [--venv PATH] [--work DIR]

Fresh clone of cogito5170/ga-sdk at <branch>, fast-forward check against the integration branch, `ga check` of the
newest reports/CMD-*.md, the full unittest suite, and baseline's own mutations (a JSON list of
{"id", "file", "find", "replace", "tests": ["tests.test_x", ...]}), each run in a separate copy.
Prints one compact JSON summary and nothing else (the long logs stay in <work>/). Integration stays a separate,
deliberate step. Standard library only.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

URL = "https://github.com/cogito5170/ga-SDK.git"
BASE = "claude/gracious-meitner-vp49xe"


def sh(*a, cwd=None, env=None, timeout=3600):
    p = subprocess.run(list(a), cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def suite(py, root, names=None, timeout=3000):
    env = dict(os.environ, PYTHONPATH=str(root))
    args = [py, "-P", "-m", "unittest"] + (list(names) if names else ["discover", "-s", "tests"])
    rc, out = sh(*args, cwd=root, env=env, timeout=timeout)
    tail = [ln for ln in out.splitlines() if ln.startswith(("Ran ", "OK", "FAILED"))]
    bad = [ln.split(" (")[0] for ln in out.splitlines() if ln.startswith(("ERROR:", "FAIL:"))]
    return rc, tail, bad[:10], out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("branch")
    ap.add_argument("--mut")
    ap.add_argument("--venv", default=os.environ.get("VERDICT_PY", sys.executable))
    ap.add_argument("--work", default=tempfile.mkdtemp(prefix="verdict-"))
    a = ap.parse_args(argv)
    work = Path(a.work)
    work.mkdir(parents=True, exist_ok=True)
    wt = work / "clone"
    shutil.rmtree(wt, ignore_errors=True)
    out = {"branch": a.branch, "work": str(work)}
    rc, msg = sh("git", "clone", "-q", "-b", a.branch, URL, str(wt))
    if rc:
        print(json.dumps({**out, "error": "clone: " + msg[-300:]}))
        return 1
    sh("git", "fetch", "-q", "origin", BASE, cwd=wt)
    out["head"] = sh("git", "rev-parse", "--short", "HEAD", cwd=wt)[1].strip()
    out["ff"] = sh("git", "merge-base", "--is-ancestor", f"origin/{BASE}", "HEAD", cwd=wt)[0] == 0
    out["diffstat"] = sh("git", "diff", "--shortstat", f"origin/{BASE}", "HEAD", cwd=wt)[1].strip()
    reps = sorted(sh("git", "diff", "--name-only", f"origin/{BASE}", "HEAD", "--", "reports/", cwd=wt)[1].split())
    if reps:
        env = dict(os.environ, PYTHONPATH=str(wt))
        rc, msg = sh(a.venv, "-P", "-m", "ga", "check", reps[-1], cwd=wt, env=env)
        out["ga_check"] = {"report": reps[-1], "rc": rc, "out": msg.strip()[-200:]}
    muts = json.loads(Path(a.mut).read_text()) if a.mut else []
    killed = {}
    for m in muts:
        mw = work / f"mut-{m['id']}"
        shutil.rmtree(mw, ignore_errors=True)
        shutil.copytree(wt, mw, symlinks=True)
        f = mw / m["file"]
        s = f.read_text(encoding="utf-8")
        if m["find"] not in s:
            killed[m["id"]] = "NOMATCH"
            continue
        f.write_text(s.replace(m["find"], m["replace"], 1), encoding="utf-8")
        rc, _, _, _ = suite(a.venv, mw, m["tests"], timeout=900)
        killed[m["id"]] = "killed" if rc else "SURVIVED"
        shutil.rmtree(mw, ignore_errors=True)
    out["mutations"] = killed
    rc, tail, bad, log = suite(a.venv, wt)
    (work / "suite.log").write_text(log, encoding="utf-8")
    out["suite"] = {"rc": rc, "tail": tail, "failing": bad}
    print(json.dumps(out, ensure_ascii=False))
    return 0 if rc == 0 and out["ff"] and all(v == "killed" for v in killed.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
