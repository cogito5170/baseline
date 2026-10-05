"""Offline tests for the agy bridge: real ga mail on temporary git repos, a fake `ga supervise`. 0 model calls."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import agy_tools  # noqa: E402
import bridge  # noqa: E402
import prompt  # noqa: E402
from ga.forms import hard, parse_text, validate  # noqa: E402
from ga.mailbox import Mailbox  # noqa: E402

DIRECTIVE = {"schema": "directive/2", "id": "CMD-AG1", "rev": 1, "to": "AGY", "after": [],
             "goal": "Summarize the project README.", "why": "bridge test",
             "scope": [{"id": "S1", "text": "read README.md"}],
             "done_when": [{"id": "D1", "text": "a three-line summary"}], "budget": {"claude_p_runs": 0}}


def git(*a, cwd=None):
    subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True, text=True)


def form(head):
    return "```ga\n" + json.dumps(head, separators=(",", ":")) + "\n```\n"


class World:
    def __init__(self):
        self.tmp = Path(tempfile.mkdtemp())
        git("init", "-q", "--bare", str(self.tmp / "origin.git"))
        for who in ("hub", "mac"):
            git("clone", "-q", str(self.tmp / "origin.git"), str(self.tmp / who))
        self.work = self.tmp / "project"
        self.work.mkdir()
        (self.work / "README.md").write_text("hello\nworld\n")
        (self.work / "ga-supervise.json").write_text(json.dumps({"schema": "ga-supervise/1", "backend": "agv",
                                                                 "model": "gpt-oss-120b-medium", "tools": {}}))
        self.cfg = {**bridge.DEFAULTS, "mailbox_repo": str(self.tmp / "mac"), "workdir": str(self.work), "pull": False}
        self.hub = Mailbox(self.tmp / "hub", sleep=lambda s: None)
        self.mac = Mailbox(self.tmp / "mac", sleep=lambda s: None)


def fake_runner(out="done.\nTOOL_NEEDED: run_tests - run the repo's unit tests\n", code=0):
    calls = []

    def run(cfg, conf, task):
        calls.append({"conf": json.loads(conf.read_text()), "task": task})
        return {"code": code, "out": out, "events": [
            {"event": "turn", "model": "gpt-oss-120b-medium", "input_tokens": 11210, "tokens": 11331, "seconds": 8.2},
            {"event": "end", "status": "done" if code == 0 else "failed", "model_turns": 1, "tool_steps": 0}]}
    run.calls = calls
    return run


class BridgeTest(unittest.TestCase):
    def setUp(self):
        self.w = World()
        self.logs = []

    def pass_(self, runner):
        return bridge.one_pass(self.w.cfg, box=self.w.mac, runner=runner, log=self.logs.append)

    def replies(self):
        return [m for m in self.w.hub.unread("baseline")]

    def test_directive_runs_and_report_returns(self):
        self.w.hub.send("AGY", form(DIRECTIVE), "baseline")
        run = fake_runner()
        self.assertEqual(self.pass_(run), 1)
        self.assertIn("Summarize the project README.", run.calls[0]["task"])
        self.assertIn("D1: a three-line summary", run.calls[0]["task"])
        self.assertIn("read_file", run.calls[0]["conf"]["tools"])  # approved tools merged in
        (msg,) = self.replies()
        head, _ = parse_text(msg.text)
        self.assertEqual(hard(validate(head)), [])
        self.assertEqual(head["handled"][0]["id"], "CMD-AG1")
        self.assertEqual(head["items"][0]["state"], "met")
        self.assertIn({"kind": "dependency", "what": "tool needed: run_tests - run the repo's unit tests"},
                      head["blockers"])
        self.assertEqual(next(r["value"] for r in head["results"] if r["name"] == "input_tokens"), 11210)
        self.assertEqual(self.pass_(fake_runner()), 0)  # read once, never run twice

    def test_each_directive_gets_its_own_state_dir(self):
        self.w.hub.send("AGY", form(DIRECTIVE), "baseline")
        run = fake_runner()
        self.pass_(run)
        self.assertEqual(run.calls[0]["conf"]["state_dir"], ".ga-supervise/CMD-AG1")

    def test_stuck_state_is_a_blocker(self):
        self.w.hub.send("AGY", form(DIRECTIVE), "baseline")
        self.pass_(fake_runner(out="[ga supervise] T1 is not finished — ga supervise --resume continues it first\n", code=1))
        head, _ = parse_text(self.replies()[0].text)
        self.assertIn("T1 unfinished", head["blockers"][0]["what"])

    def test_plan_problems_and_tool_results_reach_the_report(self):
        self.w.hub.send("AGY", form(DIRECTIVE), "baseline")
        state = self.w.work / ".ga-supervise" / "CMD-AG1"
        (state / "results").mkdir(parents=True)
        (state / "results" / "T1.r1.a.json").write_text(json.dumps({"text": "exit 0\nRan 795 tests\nOK"}))
        (state / "results" / "T1.r1.b.json").write_text(json.dumps({"text": "token " + "sk-" + "ant-api03-" + "B" * 40}))

        def run(cfg, conf, task):
            return {"code": 1, "out": "[ga supervise] T1 failed", "state": str(state), "events": [
                {"event": "turn", "input_tokens": 10000, "tokens": 10500, "seconds": 3},
                {"event": "plan", "step": "T1.m2", "ok": False, "problems": "not_json"},
                {"event": "end", "status": "failed"}]}
        self.pass_(run)
        (msg,) = self.replies()
        head, _ = parse_text(msg.text)
        self.assertIn("not a valid plan in T1.m2: not_json", head["blockers"][0]["what"])
        self.assertIn("Ran 795 tests", msg.text)
        self.assertNotIn("ant-api03", msg.text)

    def test_restart_when_code_changes(self):
        calls, old, orig = [], bridge.STAMP, bridge.os.execv
        try:
            bridge.os.execv = lambda *a: calls.append(a)
            bridge.restart_if_updated(log=lambda s: None)  # unchanged code: no restart
            self.assertEqual(calls, [])
            bridge.STAMP = "stale"
            bridge.restart_if_updated(log=lambda s: None)
        finally:
            bridge.os.execv, bridge.STAMP = orig, old
        self.assertEqual(len(calls), 1)

    def test_failed_run_is_unmet(self):
        self.w.hub.send("AGY", form(DIRECTIVE), "baseline")
        self.pass_(fake_runner(out="[ga supervise] agy refused 1 action(s) in T1.m1: command\n", code=1))
        head, _ = parse_text(self.replies()[0].text)
        self.assertEqual(head["items"][0]["state"], "unmet")
        self.assertEqual(head["blockers"][0]["kind"], "permission")

    def test_only_the_hub_may_direct(self):
        self.w.hub.send("AGY", form(DIRECTIVE), "stranger")
        run = fake_runner()
        self.pass_(run)
        self.assertEqual(run.calls, [])
        head, _ = parse_text(self.replies()[0].text)
        self.assertEqual(head["handled"][0]["status"], "declined")

    def test_secret_in_answer_is_withheld(self):
        self.w.hub.send("AGY", form(DIRECTIVE), "baseline")
        self.pass_(fake_runner(out="key " + "sk-" + "ant-api03-" + "A" * 40))
        (msg,) = self.replies()
        self.assertIn("withheld", msg.text)


class PromptTest(unittest.TestCase):
    def test_next_prints_the_directive_compactly(self):
        w = World()
        w.hub.send("AGY", form(DIRECTIVE), "baseline")
        import io
        from contextlib import redirect_stdout, redirect_stderr
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            self.assertEqual(prompt.cmd_next(str(w.tmp / "mac")), 0)
        text = out.getvalue()
        self.assertIn("Goal: Summarize the project README.", text)
        self.assertIn("- D1: a three-line summary", text)
        self.assertRegex(text, r"\(ga: \d+ tokens\)")
        self.assertEqual(len(list(w.mac.unread("AGY"))), 1)  # not marked read

    def test_refine_makes_a_valid_directive(self):
        import io
        from contextlib import redirect_stdout
        out = io.StringIO()
        with redirect_stdout(out):
            prompt.main(["refine", "--goal", "README 를 세 줄로 요약", "--scope", "읽기만", "--done", "세 줄 이하"])
        head, _ = parse_text(out.getvalue().split("--- paste")[0])
        self.assertEqual(hard(validate(head)), [])
        self.assertEqual(head["done_when"][0], {"id": "D1", "text": "세 줄 이하"})
        with self.assertRaises(SystemExit):
            prompt.main(["refine", "--goal", "x"])  # no done criterion

    def test_cap(self):
        with self.assertRaises(SystemExit):
            prompt.checked("word " * 5000)


class ToolsTest(unittest.TestCase):
    def setUp(self):
        self.old = os.getcwd()
        self.d = Path(tempfile.mkdtemp())
        (self.d / "src").mkdir()
        (self.d / "src" / "a.py").write_text("x = 1\ny = 2\n")
        (self.d / ".env").write_text("SECRET=1\n")
        os.chdir(self.d)

    def tearDown(self):
        os.chdir(self.old)

    def test_read_list_search(self):
        self.assertEqual(agy_tools.list_dir(), "src/")
        self.assertEqual(agy_tools.read_file("src/a.py", 2, 1), "2\ty = 2")
        self.assertEqual(agy_tools.search(r"y =", "."), "src/a.py:2: y = 2")

    def test_run_check_only_allowed_names(self):
        os.environ["AGY_BRIDGE_COMMANDS"] = json.dumps({"py": [sys.executable, "-c", "import os;print('ok', 'MY_API_KEY' in os.environ)"]})
        os.environ["MY_API_KEY"] = "fake"
        try:
            self.assertEqual(agy_tools.run_check("py").split(), ["exit", "0", "ok", "False"])
            with self.assertRaises(ValueError):
                agy_tools.run_check("rm")
        finally:
            del os.environ["AGY_BRIDGE_COMMANDS"], os.environ["MY_API_KEY"]

    def test_run_check_timeout_per_command(self):
        os.environ["AGY_BRIDGE_COMMANDS"] = json.dumps({
            "slow": {"argv": [sys.executable, "-c", "import time; time.sleep(3)"], "timeout_s": 1},
            "ok": {"argv": [sys.executable, "-c", "print('fine')"], "timeout_s": 99999}})
        try:
            self.assertEqual(agy_tools.run_check("slow").splitlines()[:2], ["exit 124", "timed out after 1 s"])
            self.assertEqual(agy_tools.run_check("ok").split(), ["exit", "0", "fine"])
            os.environ["AGY_BRIDGE_COMMANDS"] = json.dumps({"bad": {"argv": "rm -rf /"}})
            with self.assertRaises(ValueError):
                agy_tools.run_check("bad")  # a string is never run (no shell)
        finally:
            del os.environ["AGY_BRIDGE_COMMANDS"]

    def test_confined(self):
        for bad in ("../x", "/etc/passwd", ".env"):
            with self.assertRaises(ValueError):
                agy_tools.read_file(bad)


if __name__ == "__main__":
    unittest.main()
