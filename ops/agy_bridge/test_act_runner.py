"""Offline tests for the code-work path of the agy bridge (BD-424): real git repos, a fake `ga act`. 0 model calls."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import act_runner  # noqa: E402
import bridge  # noqa: E402
from ga.forms import hard, parse_text, validate  # noqa: E402


def git(*a, cwd=None):
    return subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True, text=True).stdout


HEAD = {"schema": "directive/2", "id": "CMD-AGA9", "rev": 1, "to": "AGY", "after": [], "goal": "g", "why": "w",
        "scope": [{"id": "S1", "text": "s"}], "done_when": [{"id": "D1", "text": "test passes"}],
        "budget": {"claude_p_runs": 0}}


class ActRunnerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        git("init", "-q", "--bare", "-b", "main", str(self.tmp / "origin.git"))
        seed = self.tmp / "seed"
        git("clone", "-q", str(self.tmp / "origin.git"), str(seed))
        (seed / "app.py").write_text("def f():\n    return 1\n")
        (seed / "frontend").mkdir()
        (seed / "frontend" / "x.txt").write_text("x\n")
        git("-c", "user.name=t", "-c", "user.email=t@x", "-C", str(seed), "add", "-A")
        git("-c", "user.name=t", "-c", "user.email=t@x", "-C", str(seed), "commit", "-qm", "init")
        git("-C", str(seed), "push", "-q", "origin", "HEAD:main")
        self.checkout = self.tmp / "token"
        git("clone", "-q", str(self.tmp / "origin.git"), str(self.checkout))
        (self.checkout / "frontend" / "node_modules").mkdir()
        (self.checkout / "app.py").write_text("user's own uncommitted edit\n")  # must survive
        self.spec = {"item": {"id": "CMD-AGA9", "goal": "make f return 2", "files": ["app.py"], "done_when": "test"},
                     "tests": {"tests/test_app.py": "from app import f\nassert f() == 2\n"},
                     "commands": {"commands": {"test": ["{venv_python}", "tests/test_app.py"]}}, "base": "main"}
        self.cfg = {"name": "AGY", "act": {"repo": str(self.checkout), "backend": "agv", "model": "gpt-oss-120b-medium"}}

    def fake_act(self, edit=True, status="done"):
        seen = {}

        def run(cfg, spec, wt, checkout):
            seen["wt"], seen["test"] = wt, (wt / "tests/test_app.py").read_text()
            seen["nm"] = (wt / "frontend" / "node_modules").is_symlink()
            if edit:
                (wt / "app.py").write_text("def f():\n    return 2\n")
            return {"code": 0 if status == "done" else 1, "out": "...\n" + json.dumps(
                {"status": status, "reason": "done_when passes" if status == "done" else "no progress", "turns": 2,
                 "tokens": {"input": 5000, "total": 5600}, "changed": ["app.py"] if edit else []}), "result": {
                "status": status, "reason": "done_when passes" if status == "done" else "no progress", "turns": 2,
                "tokens": {"input": 5000, "total": 5600}, "changed": ["app.py"] if edit else []}}
        run.seen = seen
        return run

    def test_worktree_tests_patch_and_users_checkout_untouched(self):
        run = self.fake_act()
        text = act_runner.handle(self.cfg, HEAD, runner=run, spec=self.spec)
        head, _ = parse_text(text)
        self.assertEqual(hard(validate(head)), [])
        self.assertEqual(head["items"][0]["state"], "met")
        self.assertIn("assert f() == 2", run.seen["test"])
        self.assertTrue(run.seen["nm"])
        self.assertNotEqual(run.seen["wt"], self.checkout)
        self.assertIn("+    return 2", text)
        self.assertIn("tests/test_app.py", text)  # baseline's test is part of the patch, for review
        self.assertNotIn("node_modules", text)  # the link prepare() made is not part of the change
        self.assertEqual((self.checkout / "app.py").read_text(), "user's own uncommitted edit\n")
        self.assertFalse(run.seen["wt"].exists())  # worktree removed
        self.assertIn("agv/CMD-AGA9", git("-C", str(self.checkout), "branch"))

    def test_the_agv_commit_is_pushed_and_named_in_the_report(self):
        text = act_runner.handle(self.cfg, HEAD, runner=self.fake_act(), spec=self.spec)
        head, _ = parse_text(text)
        self.assertEqual(hard(validate(head)), [])
        c = head["commits"][0]
        self.assertEqual((c["repo"], c["branch"]), ("cogito5170/Token", "agv/CMD-AGA9-r1"))
        remote = git("-C", str(self.tmp / "origin.git"), "rev-parse", "refs/heads/agv/CMD-AGA9-r1").strip()
        self.assertEqual(c["sha"], remote)
        self.assertNotIn("+    return 2", git("-C", str(self.tmp / "origin.git"), "show", "main:app.py"))  # base untouched

    def test_no_push_for_a_withheld_patch_or_when_push_is_off(self):
        def secret(cfg, spec, wt, checkout):
            (wt / "app.py").write_text("KEY = '" + "sk-" + "ant-api03-" + "C" * 40 + "'\n")
            return {"code": 0, "out": "", "result": {"status": "done", "turns": 1, "tokens": {}, "changed": ["app.py"]}}
        for cfg, run in ((self.cfg, secret), (dict(self.cfg, act=dict(self.cfg["act"], push=False)), self.fake_act())):
            head, _ = parse_text(act_runner.handle(cfg, HEAD, runner=run, spec=self.spec))
            self.assertNotIn("commits", head)
        refs = git("-C", str(self.tmp / "origin.git"), "for-each-ref", "--format=%(refname)")
        self.assertNotIn("agv/", refs)

    def test_not_done_is_unmet_with_blocker(self):
        text = act_runner.handle(self.cfg, HEAD, runner=self.fake_act(edit=False, status="blocked"), spec=self.spec)
        head, _ = parse_text(text)
        self.assertEqual(head["items"][0]["state"], "unmet")
        self.assertIn("no progress", head["blockers"][0]["what"])

    def test_bad_test_path_refused(self):
        for bad in ("../x.py", "/etc/x", ".git/hooks/pre-commit", ".env"):
            spec = dict(self.spec, tests={bad: "x"})
            with self.assertRaises(ValueError):
                act_runner.prepare(spec, self.checkout, "CMD-AGA9")

    def test_secret_in_patch_is_withheld(self):
        def run(cfg, spec, wt, checkout):
            (wt / "app.py").write_text("KEY = '" + "sk-" + "ant-api03-" + "C" * 40 + "'\n")
            return {"code": 0, "out": "", "result": {"status": "done", "turns": 1, "tokens": {}, "changed": ["app.py"]}}
        text = act_runner.handle(self.cfg, HEAD, runner=run, spec=self.spec)
        self.assertNotIn("ant-api03", text)
        self.assertIn("withheld", text)

    def test_rewrite_removes_the_owned_file_in_the_worktree_only(self):
        seen = {}

        def run(cfg, spec, wt, checkout):
            seen["gone"] = not (wt / "app.py").exists()
            (wt / "app.py").write_text("def f():\n    return 2\n")
            return {"code": 0, "out": "", "result": {"status": "done", "turns": 1, "tokens": {}, "changed": ["app.py"]}}
        text = act_runner.handle(self.cfg, HEAD, runner=run, spec=dict(self.spec, rewrite=["app.py"]))
        self.assertTrue(seen["gone"])
        self.assertIn("+    return 2", text)
        self.assertEqual((self.checkout / "app.py").read_text(), "user's own uncommitted edit\n")

    def test_rewrite_only_for_the_items_files(self):
        for bad in ("tests/test_app.py", "../x.py", "/etc/passwd", "frontend/x.txt"):
            with self.assertRaises(ValueError):
                act_runner.prepare(dict(self.spec, rewrite=[bad]), self.checkout, "CMD-AGA9")

    def test_item_model_overrides_the_bridge_model(self):
        seen = {}

        def run(cfg, spec, wt, checkout):
            seen["model"] = cfg["act"]["model"]
            return {"code": 0, "out": "", "result": {"status": "done", "turns": 1, "tokens": {}, "changed": []}}
        text = act_runner.handle(self.cfg, HEAD, runner=run, spec=dict(self.spec, model="gemini-3.8-flash-high"))
        self.assertEqual(seen["model"], "gemini-3.8-flash-high")
        self.assertIn("gemini-3.8-flash-high", text)
        self.assertEqual(self.cfg["act"]["model"], "gpt-oss-120b-medium")  # the bridge config itself is not changed
        for bad in ("--dangerously-skip-permissions", "a b", "../x", "gemini-9-ultra", "claude-opus-5-5"):
            with self.assertRaises(ValueError):
                act_runner.handle(self.cfg, HEAD, runner=run, spec=dict(self.spec, model=bad))

    def test_item_agent_overrides_or_drops_the_bridge_agent(self):
        seen = []

        def run(cfg, spec, wt, checkout):
            seen.append(cfg["act"].get("options"))
            return {"code": 0, "out": "", "result": {"status": "done", "turns": 1, "tokens": {}, "changed": []}}
        cfg = dict(self.cfg, act=dict(self.cfg["act"], options={"agent": "ga-act", "x": 1}))
        act_runner.handle(cfg, HEAD, runner=run, spec=dict(self.spec, agent="minimal"))
        act_runner.handle(cfg, HEAD, runner=run, spec=dict(self.spec, agent=""))
        self.assertEqual(seen, [{"agent": "minimal", "x": 1}, {"x": 1}])
        with self.assertRaises(ValueError):
            act_runner.handle(cfg, HEAD, runner=run, spec=dict(self.spec, agent="a;b"))

    def test_ladder_reaches_ga_act_argv_and_unknown_models_are_refused(self):
        seen = {}
        old = act_runner.subprocess.run

        def fake_run(argv, **kw):
            seen["argv"] = argv
            return act_runner.subprocess.CompletedProcess(argv, 0, '{"status": "done", "turns": 1, "tokens": {}}', "")
        try:
            act_runner.subprocess.run = fake_run
            wt = act_runner.prepare(self.spec, self.checkout, "CMD-AGA9")
            act_runner.run_act(self.cfg, dict(self.spec, ladder=["gpt-oss-120b-medium", "gemini-3.1-pro-high"]), wt,
                               self.checkout)
        finally:
            act_runner.subprocess.run = old
        i = seen["argv"].index("--ladder")
        self.assertEqual(seen["argv"][i + 1], "gpt-oss-120b-medium,gemini-3.1-pro-high")
        with self.assertRaises(ValueError):
            act_runner.run_act(self.cfg, dict(self.spec, ladder=["gpt-oss-120b-medium", "x; rm"]), wt, self.checkout)

    def test_routed_by_default_with_a_lasting_state_dir_and_ladder_wins(self):
        seen = []
        old = act_runner.subprocess.run

        def fake_run(argv, **kw):
            seen.append(argv)
            return act_runner.subprocess.CompletedProcess(argv, 0, '{"status": "done", "turns": 1, "tokens": {}}', "")
        cfg = dict(self.cfg, act=dict(self.cfg["act"], state_dir=str(self.tmp / "act-state")))
        wt = act_runner.prepare(self.spec, self.checkout, "CMD-AGA9")
        act_runner._HELP["act"] = "usage: ga act ... --route ..."
        self.addCleanup(act_runner._HELP.clear)
        try:
            act_runner.subprocess.run = fake_run
            act_runner.run_act(cfg, self.spec, wt, self.checkout)
            act_runner.run_act(cfg, dict(self.spec, triage_compare=["gemini-3.1-pro-high", "claude-opus-5-5-high"]),
                               wt, self.checkout)
            act_runner.run_act(cfg, dict(self.spec, ladder=["gpt-oss-120b-medium"]), wt, self.checkout)
            act_runner.run_act(cfg, dict(self.spec, route=False), wt, self.checkout)
        finally:
            act_runner.subprocess.run = old
        a = seen[0]
        self.assertIn("--route", a)
        self.assertEqual(a[a.index("--state") + 1], str(self.tmp / "act-state"))  # outlives the run: the route ledger
        self.assertEqual(seen[1][seen[1].index("--triage-compare") + 1], "gemini-3.1-pro-high,claude-opus-5-5-high")
        self.assertNotIn("--route", seen[2])  # an explicit ladder is not routed
        self.assertNotIn("--route", seen[3])
        self.assertNotEqual(seen[3][seen[3].index("--state") + 1], str(self.tmp / "act-state"))
        with self.assertRaises(ValueError):
            act_runner.run_act(cfg, dict(self.spec, triage_compare=["x", "y"]), wt, self.checkout)
        act_runner._HELP["act"] = "usage: ga act (an older ga without routing)"
        seen.clear()
        try:
            act_runner.subprocess.run = fake_run
            act_runner.run_act(cfg, self.spec, wt, self.checkout)
        finally:
            act_runner.subprocess.run = old
        self.assertNotIn("--route", seen[0])  # an older ga on the VM still runs the item

    def test_an_item_may_land_in_the_baseline_clone(self):
        seen = {}

        def run(cfg, spec, wt, checkout):
            seen["checkout"], seen["name"] = checkout, cfg["act"]["repo_name"]
            return {"code": 0, "out": "", "result": {"status": "done", "turns": 1, "tokens": {}, "changed": []}}
        cfg = dict(self.cfg, mailbox_repo=str(self.checkout))  # a clone with origin, standing in for ~/baseline
        act_runner.handle(dict(cfg, act=dict(self.cfg["act"], repo="/nonexistent")), HEAD, runner=run,
                          spec=dict(self.spec, repo="baseline"))
        self.assertEqual((seen["checkout"], seen["name"]), (self.checkout.resolve(), "cogito5170/baseline"))
        with self.assertRaises(ValueError):
            act_runner.handle(cfg, HEAD, runner=run, spec=dict(self.spec, repo="../elsewhere"))

    def test_placeholders_expand(self):
        self.assertEqual(act_runner._expand(["{venv_python}", "-m", "x"], {"venv_python": "/v/bin/python"}),
                         ["/v/bin/python", "-m", "x"])

    def setUp_items(self):
        d = act_runner.HERE / "items"
        d.mkdir(exist_ok=True)
        return d

    def test_bridge_routes_item_directives_to_act(self):
        calls = []
        old = bridge.act
        try:
            bridge.act = lambda cfg, head: calls.append(head["id"]) or act_runner.report(
                {"name": "AGY"}, head, {"code": 0, "out": "", "result": {"status": "done", "turns": 1, "tokens": {}}}, "")
            d = self.setUp_items()
            f = d / "CMD-AGA9.json"
            f.write_text(json.dumps(self.spec))
            try:
                from test_bridge import World, form, fake_runner
                w = World()
                w.hub.send("AGY", form(HEAD), "baseline")
                run = fake_runner()
                bridge.one_pass(w.cfg, box=w.mac, runner=run, log=lambda s: None)
                self.assertEqual(calls, ["CMD-AGA9"])
                self.assertEqual(run.calls, [])  # ga supervise not used
            finally:
                f.unlink()
        finally:
            bridge.act = old


if __name__ == "__main__":
    unittest.main()
