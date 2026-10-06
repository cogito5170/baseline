"""The VM bridge's policy gate (user 10-06): every push the bridge makes goes through ops/flow/judge.py first.

The gate decides nothing itself. It gathers the facts (action, policy + its sha, usage counts, stop switch, prior
verdict for the same action), asks judge.py, and:
  allow         -> executes, with no per-action human step;
  human_review  -> does not execute; the action and what it would do are held for the user;
  deny/conflict -> does not execute; held with the verdict, so a later attempt of the same action (another command,
                   session or host has the same key) gets the same answer under the same policy.
Every check is written to the audit log. The audit log is never read back as an input to a verdict.

On the VM, by a person:
    python3 ops/agy_bridge/gate.py stop|start [--config ~/agy-bridge.json]   stop switch (start clears the VM file only)
    python3 ops/agy_bridge/gate.py held [--config ...]                       what waits for the user
    python3 ops/agy_bridge/gate.py approve <key> [--config ...]              your approval of exactly that action:
                                                                             judged again, executed only on allow

Stop switch: either file present = stopped: ~/agy-bridge.STOP (VM) or ops/agy_bridge/STOP (committed). Stopped, no
new push, mail, session, agent or hand-off starts and no new directive is picked up. A `ga act` / `ga supervise` run
already started finishes in its own worktree up to its timeout (nothing it produces leaves the VM: its push and its
report are held).

Config (optional "gate" in ~/agy-bridge.json): {"policy": path, "policy_sha": "<12 hex>", "state_dir": path,
"stop_files": [...]}. policy defaults to ops/flow/policy.json of this clone. Without policy_sha it must equal the
committed version. Limits come from policy.json (or judge.LIMITS), never from this config.
"""
from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "flow"))
import judge  # noqa: E402

DEFAULTS = {"policy": str(HERE.parent / "flow" / "policy.json"), "policy_sha": None, "state_dir": "~/.ga/bridge-gate",
            "stop_files": ["~/agy-bridge.STOP", str(HERE / "STOP")]}


class Gate:
    def __init__(self, cfg: dict[str, Any]):
        g = {**DEFAULTS, **(cfg.get("gate") or {})}
        self.policy = Path(g["policy"]).expanduser()
        self.pinned = g["policy_sha"]
        self.dir = Path(g["state_dir"]).expanduser()
        self.stop_files = [Path(p).expanduser() for p in g["stop_files"]]
        self.session_id = f"{cfg.get('name', 'AGY')}@{socket.gethostname()}"
        self.cfg = cfg

    # -- state (usage counters, held actions): an input to judge.py; the audit log is not
    def _state(self) -> dict[str, Any]:
        try:
            return json.loads((self.dir / "state.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _save(self, st: dict[str, Any]) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        tmp = self.dir / "state.json.tmp"
        tmp.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(self.dir / "state.json")

    def stopped(self) -> bool:
        return any(p.exists() for p in self.stop_files)

    def check(self, act: dict[str, Any], count: bool = True) -> dict[str, Any]:
        """judge.py's verdict for this action, with the facts the gate holds added. count=False: a dry look."""
        st = self._state()
        key = judge.action_key(act)
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        pol, sha, problem = judge.load_policy(self.policy, self.pinned)
        seen = st.get("attempts", {}).get(key) or {}
        attempts = int(seen.get("n", 0)) if seen.get("policy_sha") == sha else 0  # retries count under this policy only
        held = st.get("held", {}).get(key)
        facts = {**act, "session": act.get("session") or self.session_id, "stop": self.stopped(),
                 "usage": {**(act.get("usage") or {}), "pushes": int(st.get("pushes", {}).get(day, 0)),
                           "retries": attempts},
                 "prior": [*(act.get("prior") or []),
                           *([{"by": "flow", "decision": held["decision"], "policy_sha": held["policy_sha"]}] if held else [])]}
        v = judge.judge(facts, pol, judge._verdicts(judge.VERDICTS), sha, problem)
        v["policy_version"] = (pol or {}).get("schema")
        if count:
            st.setdefault("attempts", {})[key] = {"n": attempts + 1, "policy_sha": sha}
            self._save(st)
        return v

    def execute(self, act: dict[str, Any], payload: dict[str, Any], run: Callable[[], Any] | None = None,
                approved_by: str = "") -> tuple[dict[str, Any], str]:
        """Execute payload only if judge.py says allow; otherwise hold it. Returns (verdict, result)."""
        v = self.check(act)
        if v["decision"] == "allow":
            try:
                (run or (lambda: run_payload(payload)))()
                result = "ok"
                st = self._state()
                if act.get("kind") in ("push", "integrate"):
                    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                    st.setdefault("pushes", {})[day] = int(st.get("pushes", {}).get(day, 0)) + 1
                st.get("held", {}).pop(v["key"], None)
                self._save(st)
            except Exception as e:  # noqa: BLE001 — recorded, never retried here
                result = f"failed: {type(e).__name__}: {str(e)[:200]}"
        else:
            st = self._state()
            st.setdefault("held", {})[v["key"]] = {"action": act, "payload": payload, "decision": v["decision"],
                                                    "policy_sha": v["policy_sha"], "reasons": v["reasons"],
                                                    "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            self._save(st)
            result = "held" if v["decision"] == "human_review" else "not run"
        self.audit(act, v, result, approved_by)
        return v, result

    def audit(self, act: dict[str, Any], v: dict[str, Any], result: str, approved_by: str = "") -> None:
        src = approved_by or ",".join(sorted({a.get("source", "?") for a in act.get("approvals") or []})) or "policy"
        row = {"action": act.get("kind"), "key": v["key"], "verdict": v["decision"],
               "policy_version": v.get("policy_version"), "policy_hash": v["policy_sha"],
               "repository": act.get("repo"), "branch": act.get("branch"), "commit": act.get("sha"),
               "session_id": act.get("session") or self.session_id, "approval_source": src,
               "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"), "result": result,
               "reasons": [r["reason"] for r in v["reasons"]][:6]}
        self.dir.mkdir(parents=True, exist_ok=True)
        with (self.dir / "audit.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def held(self) -> dict[str, Any]:
        return self._state().get("held", {})

    def approve(self, key: str, who: str = "user on the VM") -> tuple[dict[str, Any], str]:
        """The user's approval of exactly one held action: judged again with it; executed only on allow."""
        h = self.held().get(key)
        if not h:
            raise KeyError(f"no held action {key}")
        act = {**h["action"], "approvals": [*(h["action"].get("approvals") or []),
                                            {"source": "user_direct", "via": "gate approve", "key": key}]}
        st = self._state()
        st["held"].pop(key)  # the held verdict is replaced by this new judgement (it is held again unless allowed)
        st.get("attempts", {}).pop(key, None)
        self._save(st)
        return self.execute(act, h["payload"], approved_by=f"user_direct ({who})")


def run_payload(p: dict[str, Any]) -> None:
    """The only things the gate executes: a plain (never forced) git push of one sha to one branch, or one mail."""
    if p.get("type") == "git_push":
        r = subprocess.run(["git", "-C", p["repo_dir"], "push", "-q", p.get("remote", "origin"),
                            f"{p['sha']}:refs/heads/{p['branch']}"], capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError(r.stderr.strip()[:200])
    elif p.get("type") == "mail":
        from ga.mailbox import Mailbox
        Mailbox(p["mailbox_repo"]).send(p["to"], p["text"], p["sender"])
    else:
        raise ValueError(f"unknown payload type {p.get('type')!r}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", choices=["stop", "start", "held", "approve"])
    ap.add_argument("key", nargs="?")
    ap.add_argument("--config", default="~/agy-bridge.json")
    a = ap.parse_args(argv)
    p = Path(a.config).expanduser()
    g = Gate(json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {})
    if a.cmd == "stop":
        g.stop_files[0].touch()
        print(f"stopped: {g.stop_files[0]}")
    elif a.cmd == "start":
        g.stop_files[0].unlink(missing_ok=True)
        print("VM stop file removed" + ("; still stopped by " + ", ".join(map(str, filter(Path.exists, g.stop_files)))
                                        if g.stopped() else ""))
    elif a.cmd == "held":
        for k, h in g.held().items():
            act = h["action"]
            print(f"{k}  {h['decision']:<12} {act.get('kind')} {act.get('repo')} {act.get('branch')} {act.get('sha') or ''}"
                  f"\n    {'; '.join(r['reason'] for r in h['reasons'])[:300]}")
    else:
        if not a.key:
            ap.error("approve needs the key (see: held)")
        v, result = g.approve(a.key)
        print(json.dumps({"decision": v["decision"], "result": result, "reasons": v["reasons"]}, ensure_ascii=False, indent=1))
        return 0 if result == "ok" else 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
