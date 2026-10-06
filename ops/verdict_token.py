"""One-call verdict for a Token agv branch (sibling of ops/verdict.py, which is ga-sdk only).

usage: python3 ops/verdict_token.py <branch> --item ops/agy_bridge/items/<id>.json --mut <mut.json> [--token /home/user/token]
Worktree of <branch> from the local Token clone (fetched first), fast-forward check against the integration branch,
baseline's acceptance tests byte-identical, the item's test command, the full suite of the touched side (frontend vitest
and/or backend unittest), then each mutation [{"file", "old", "new"}] must make the item's test command fail.
Prints one JSON line; exit 0 only if everything is green.
"""
import argparse, json, os, subprocess, sys, tempfile

INTEG = "claude/gracious-meitner-vp49xe"


def sh(cmd, cwd, timeout=900):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout + p.stderr)[-400:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("branch")
    ap.add_argument("--item", required=True)
    ap.add_argument("--mut", required=True)
    ap.add_argument("--token", default="/home/user/token")
    a = ap.parse_args()
    item, muts = json.load(open(a.item)), json.load(open(a.mut))
    t = a.token
    sh(["git", "fetch", "-q", "origin", f"+refs/heads/{a.branch}:refs/remotes/origin/{a.branch}",
        f"+refs/heads/{INTEG}:refs/remotes/origin/{INTEG}"], t)
    out = {"branch": a.branch, "id": item["item"]["id"]}
    out["sha"] = sh(["git", "rev-parse", "--short", f"origin/{a.branch}"], t)[1].strip()
    out["ff"] = sh(["git", "merge-base", "--is-ancestor", f"origin/{INTEG}", f"origin/{a.branch}"], t)[0] == 0
    changed = sh(["git", "diff", "--name-only", f"origin/{INTEG}", f"origin/{a.branch}"], t)[1].split()
    allowed = set(item["item"]["files"]) | set(item["tests"])
    out["outside_scope"] = [f for f in changed if f not in allowed]
    wt = tempfile.mkdtemp(prefix="vt-")
    sh(["git", "worktree", "add", "-q", "--detach", wt, f"origin/{a.branch}"], t)
    try:
        nm = os.path.join(t, "frontend", "node_modules")
        if os.path.isdir(nm):
            os.symlink(nm, os.path.join(wt, "frontend", "node_modules"))
        out["tests_identical"] = all(
            os.path.exists(os.path.join(wt, p)) and open(os.path.join(wt, p)).read() == body
            for p, body in item["tests"].items())
        cmd = item["commands"]["commands"]["test"]
        rc, tail = sh(cmd, wt)
        out["accept"] = rc == 0
        if rc:
            out["accept_tail"] = tail
        suites = {}
        if any(f.startswith("frontend/") for f in changed):
            rc, tail = sh(["node", "frontend/node_modules/vitest/vitest.mjs", "run", "--root", "frontend"], wt)
            suites["frontend"] = rc == 0 or tail
        if any(f.startswith("backend/") for f in changed):
            rc, tail = sh([sys.executable, "-m", "unittest", "discover", "-s", "app/domains", "-t", ".", "-q"],
                          os.path.join(wt, "backend"))
            suites["backend"] = rc == 0 or tail
        out["suites"] = suites
        killed = []
        for m in muts:
            p = os.path.join(wt, m["file"])
            src = open(p).read()
            if m["old"] not in src:
                killed.append("not-applied")
                continue
            open(p, "w").write(src.replace(m["old"], m["new"], 1))
            killed.append(sh(cmd, wt)[0] != 0)
            open(p, "w").write(src)
        out["mutations"] = f"{sum(k is True for k in killed)}/{len(muts)}"
        out["mut_detail"] = killed
    finally:
        sh(["git", "worktree", "remove", "--force", wt], t)
    out["green"] = (out["ff"] and not out["outside_scope"] and out["tests_identical"] and out["accept"]
                    and all(v is True for v in out["suites"].values()) and all(k is True for k in out["mut_detail"]))
    print(json.dumps(out, ensure_ascii=False))
    sys.exit(0 if out["green"] else 1)


if __name__ == "__main__":
    main()
