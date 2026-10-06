"""Offline tests for the bridge's policy gate (gate.py -> ops/flow/judge.py): real git repos, 0 model calls.

Runs with the standard library alone; when ga-sdk is not installed, ga.mailbox / ga.forms are stubbed (only the
bridge's declined-reply path is exercised here; test_bridge.py covers real ga mail).
    python3 -m unittest test_gate        (in ops/agy_bridge)
"""
import json
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
try:
    import ga.mailbox  # noqa: F401
except ImportError:  # stub the two ga modules the bridge imports
    ga = types.ModuleType("ga")
    mb, fm = types.ModuleType("ga.mailbox"), types.ModuleType("ga.forms")
    mb.Mailbox, mb.MailError, mb.secrets_in = object, RuntimeError, lambda s: False
    fm.FormError, fm.hard, fm.validate, fm.parse_text = ValueError, lambda p: [], lambda h: [], lambda t: ({}, "")
    sys.modules.update({"ga": ga, "ga.mailbox": mb, "ga.forms": fm})
import act_runner  # noqa: E402
import bridge  # noqa: E402
import gate  # noqa: E402
import judge  # noqa: E402


def git(*a):
    return subprocess.run(["git", *a], check=True, capture_output=True, text=True).stdout


POLICY = {"schema": "policy/1",
          "auto_integrate": {"never": ["force push", "any other ref", "PRs", "secrets"], "change": "only the user"},
          "bridge": {"push": {"cogito5170/Token": ["agv/"]}, "mail": {"cogito5170/baseline": ["ga-mailbox"]},
                     "sessions": {"agent_types": ["worker"], "scopes": ["R1"], "permissions": ["read", "push_agv"],
                                  "repos": {"cogito5170/Token": ["agv/"]}}}}
HEAD = {"id": "CMD-T1", "rev": 1}


class GateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        git("init", "-q", "--bare", "-b", "main", str(self.tmp / "origin.git"))
        git("init", "-q", "--bare", "-b", "main", str(self.tmp / "other.git"))
        self.co = self.tmp / "token"
        git("clone", "-q", str(self.tmp / "origin.git"), str(self.co))
        (self.co / "app.py").write_text("x = 1\n")
        git("-C", str(self.co), "-c", "user.name=t", "-c", "user.email=t@x", "commit", "-qam", "x", "--allow-empty")
        git("-C", str(self.co), "add", "-A")
        git("-C", str(self.co), "-c", "user.name=t", "-c", "user.email=t@x", "commit", "-qm", "app")
        git("-C", str(self.co), "branch", "agv/CMD-T1")
        self.sha = git("-C", str(self.co), "rev-parse", "HEAD").strip()
        self.policy = self.tmp / "policy.json"
        self.write_policy(POLICY)

    def write_policy(self, pol, raw=None):
        self.policy.write_text(raw if raw is not None else json.dumps(pol))
        self.cfg = self.make_cfg()

    def make_cfg(self, name="AGY", state="state"):
        return {"name": name, "act": {"repo_name": "cogito5170/Token"},
                "gate": {"policy": str(self.policy), "policy_sha": judge._sha(self.policy),
                         "state_dir": str(self.tmp / state), "stop_files": [str(self.tmp / "STOP")]}}

    def remote_has(self, branch, repo="origin.git"):
        refs = git("-C", str(self.tmp / repo), "for-each-ref", "--format=%(refname)")
        return f"refs/heads/{branch}" in refs

    def publish(self, cfg=None):
        return act_runner.publish(cfg or self.cfg, self.co, HEAD, "From x\n")

    def push(self, **kw):
        return {"kind": "push", "repo": "cogito5170/Token", "branch": "agv/CMD-T1-r1", "sha": self.sha,
                "files": ["app.py"], **kw}

    def payload(self, remote="origin"):
        return {"type": "git_push", "repo_dir": str(self.co), "remote": remote, "sha": self.sha, "branch": "agv/CMD-T1-r1"}

    # 1
    def test_push_inside_policy_is_allowed_and_runs_unattended(self):
        c = self.publish()
        self.assertEqual(c, {"repo": "cogito5170/Token", "branch": "agv/CMD-T1-r1", "sha": self.sha})
        self.assertTrue(self.remote_has("agv/CMD-T1-r1"))
        row = json.loads((self.tmp / "state" / "audit.jsonl").read_text().splitlines()[-1])
        for k in ("action", "verdict", "policy_version", "policy_hash", "repository", "branch", "commit", "session_id",
                  "approval_source", "timestamp", "result"):
            self.assertIn(k, row)
        self.assertEqual((row["verdict"], row["result"], row["policy_version"]), ("allow", "ok", "policy/1"))

    # 2
    def test_action_outside_policy_is_held_for_the_user(self):
        self.write_policy({**POLICY, "bridge": {}})
        c = self.publish()
        self.assertEqual((c["decision"], c["result"]), ("human_review", "held"))
        self.assertFalse(self.remote_has("agv/CMD-T1-r1"))
        self.assertIn(c["held"], gate.Gate(self.cfg).held())
        # the user approves exactly that action -> judged again -> runs
        v, result = gate.Gate(self.cfg).approve(c["held"])
        self.assertEqual((v["decision"], result), ("allow", "ok"))
        self.assertTrue(self.remote_has("agv/CMD-T1-r1"))

    # 3
    def test_forbidden_action_is_denied_and_not_run(self):
        g = gate.Gate(self.cfg)
        v, result = g.execute(self.push(refs=["force push"]), self.payload())
        self.assertEqual((v["decision"], result), ("deny", "not run"))
        self.assertFalse(self.remote_has("agv/CMD-T1-r1"))
        v, result = g.approve(v["key"])  # the user's approval never lifts a deny
        self.assertEqual((v["decision"], result), ("deny", "not run"))
        self.assertFalse(self.remote_has("agv/CMD-T1-r1"))

    # 4, 5 (+ unknown schema, hash mismatch, not committed without a pin)
    def test_missing_or_corrupt_policy_is_deny(self):
        cases = {"missing": None, "corrupt": "{not json", "schema": json.dumps({**POLICY, "schema": "policy/9"})}
        for name, raw in cases.items():
            if raw is None:
                self.policy.unlink(missing_ok=True)
                self.cfg = self.make_cfg()
            else:
                self.write_policy(None, raw)
            self.assertEqual(self.publish()["decision"], "deny", name)
        self.write_policy(POLICY)
        self.cfg["gate"]["policy_sha"] = "0" * 12
        self.assertEqual(self.publish()["decision"], "deny", "pinned sha mismatch")
        self.cfg["gate"]["policy_sha"] = None
        self.assertEqual(self.publish()["decision"], "deny", "uncommitted, no pin")
        self.assertFalse(self.remote_has("agv/CMD-T1-r1"))

    # 6
    def test_relayed_approval_inside_the_rule_is_allowed(self):
        v, result = gate.Gate(self.cfg).execute(
            self.push(approvals=[{"source": "relayed", "via": "flow", "grants": ["push"]}]), self.payload())
        self.assertEqual((v["decision"], result), ("allow", "ok"))

    # 7
    def test_relayed_approval_beyond_the_rule_does_not_run(self):
        v, result = gate.Gate(self.cfg).execute(
            self.push(approvals=[{"source": "relayed", "via": "flow", "grants": ["push", "policy_change"]}]), self.payload())
        self.assertEqual((v["decision"], result), ("conflict", "not run"))
        self.assertFalse(self.remote_has("agv/CMD-T1-r1"))

    # 8
    def test_same_action_in_a_new_session_gets_the_same_verdict(self):
        for act in (self.push(), self.push(branch="main"), self.push(refs=["force push"])):
            a = gate.Gate(self.make_cfg("AGY", "s1")).check(act, count=False)
            b = gate.Gate(self.make_cfg("AGY-2", "s2")).check({**act, "session": "session_new"}, count=False)
            self.assertEqual((a["decision"], a["key"]), (b["decision"], b["key"]))

    # 9, 10
    def test_permission_widening_and_session_limit_go_to_the_user(self):
        g = gate.Gate(self.cfg)
        ses = {"kind": "agent_create", "agent_type": "worker", "scope": "R1", "repo": "cogito5170/Token", "branch": "agv/x",
               "permissions": ["read"], "controller_permissions": ["read"], "usage": {"sessions": 1, "children": 0}}
        self.assertEqual(g.check(ses, count=False)["decision"], "allow")
        self.assertEqual(g.check({**ses, "permissions": ["read", "push_agv"]}, count=False)["decision"], "human_review")
        self.assertEqual(g.check({**ses, "usage": {"sessions": 5}}, count=False)["decision"], "human_review")
        self.assertEqual(g.check({**ses, "usage": {"sessions": 1, "children": 3}}, count=False)["decision"], "human_review")
        self.assertEqual(g.check({**ses, "max_runtime_s": 99999}, count=False)["decision"], "human_review")

    def test_push_limit_and_retry_limit_go_to_the_user(self):
        st = self.tmp / "state"
        st.mkdir()
        day = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%d")
        (st / "state.json").write_text(json.dumps({"pushes": {day: 20}}))
        self.assertEqual(self.publish()["decision"], "human_review")
        g = gate.Gate(self.make_cfg(state="s3"))
        decisions = [g.check({**self.push(), "kind": "mail", "repo": "cogito5170/baseline", "branch": "ga-mailbox"})["decision"]
                     for _ in range(3)]
        self.assertEqual(decisions, ["allow", "allow", "human_review"])  # max_retries 1
        mails = [g.check({"kind": "mail", "repo": "cogito5170/baseline", "branch": "ga-mailbox", "directive": "CMD-X1",
                          "content": c})["decision"] for c in ("a", "b", "c")]
        self.assertEqual(mails, ["allow"] * 3)  # different replies are different actions, not retries

    # 11
    def test_stop_switch_starts_nothing_new(self):
        (self.tmp / "STOP").touch()
        c = self.publish()
        self.assertEqual((c["decision"], c["result"]), ("human_review", "held"))
        self.assertFalse(self.remote_has("agv/CMD-T1-r1"))
        v, result = gate.Gate(self.cfg).approve(c["held"])  # not even the user's approval while stopped
        self.assertEqual(result, "held")
        self.assertFalse(self.remote_has("agv/CMD-T1-r1"))

        class Box:
            read = False

            def unread(self, name):
                Box.read = True
                return []
        logs = []
        self.assertEqual(bridge.one_pass({**self.cfg, "pull": False}, box=Box(), log=logs.append), 0)
        self.assertFalse(Box.read)
        self.assertIn("stop switch", logs[0])

    # 12
    def test_a_refused_action_is_not_rerouted(self):
        g = gate.Gate(self.cfg)
        v, _ = g.execute(self.push(branch="main"), {**self.payload(), "branch": "main"})
        self.assertEqual(v["decision"], "human_review")
        # same outcome, other command / session / host / agent: same key, the held verdict stands, nothing runs
        other = gate.Gate({**self.cfg, "name": "AGY-other-vm"})
        v2, r2 = other.execute(self.push(branch="main", session="session_other", via="agent-2"),
                               {**self.payload(remote=str(self.tmp / "other.git")), "branch": "main"})
        self.assertEqual((v2["key"], v2["decision"], r2), (v["key"], "human_review", "held"))
        self.assertTrue(any("prior human_review stands" in r["reason"] for r in v2["reasons"]))
        self.assertFalse(self.remote_has("main", "other.git"))
        # a changed policy is judged again rather than repeating the old verdict
        self.write_policy({**POLICY, "bridge": {**POLICY["bridge"], "push": {"cogito5170/Token": ["agv/", "main"]}}})
        self.assertEqual(gate.Gate(self.cfg).check(self.push(branch="main"), count=False)["decision"], "allow")

    def test_audit_log_is_not_an_input(self):
        g = gate.Gate(self.cfg)
        before = g.check(self.push(), count=False)["decision"]
        (self.tmp / "state").mkdir(exist_ok=True)
        (self.tmp / "state" / "audit.jsonl").write_text('{"verdict": "deny"}\nnot json\n')
        self.assertEqual(g.check(self.push(), count=False)["decision"], before)

    def test_bridge_report_mail_goes_through_the_gate(self):
        sent = []

        class Msg:
            sender, schema, form, valid, problems, path, text = "stranger", "directive/2", "CMD-X1", True, [], "p", ""

        class Box:
            def unread(self, name):
                return [Msg()]

            def send(self, to, text, sender):
                sent.append(to)

            def mark_read(self, name, path):
                pass
        cfg = {**self.cfg, "pull": False, "hub": "baseline", "mailbox_repo": str(self.tmp)}
        bridge.one_pass(cfg, box=Box(), log=lambda s: None)
        self.assertEqual(sent, ["baseline"])  # inside bridge.mail -> sent
        self.write_policy({**POLICY, "bridge": {"push": POLICY["bridge"]["push"]}})
        logs = []
        bridge.one_pass({**cfg, "gate": self.make_cfg(state="s4")["gate"]}, box=Box(), log=logs.append)
        self.assertEqual(sent, ["baseline"])  # no mail rule -> held, not sent
        self.assertTrue(any("held by judge.py" in s for s in logs))


if __name__ == "__main__":
    unittest.main()
