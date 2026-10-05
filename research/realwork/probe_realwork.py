"""Probe: can ga 0.6 peer pool run a large real development task as-is? Fake backends, 0 model calls.
Each test asserts the CURRENT behaviour; a test that fails later means ga gained the capability."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, "/home/user/ga-sdk/tests")
sys.path.insert(0, "/home/user/ga-sdk")
import net_world as nw
from ga.net import pool as P
from ga import judge as J
from ga.backends.builtin import ClaudeRunner
sys.path.insert(0, "/home/user/ga-sdk/tests")
from test_ga33 import network, item, PoolCase


class RealWork(PoolCase):
    def test_R1_no_dependency_field(self):
        self.world()
        ok, why = self.pool().add(item("CMD-B1", after=["CMD-A1"]))
        self.assertFalse(ok); self.assertIn("after", why)

    def test_R2_dependent_items_start_together(self):
        # contract item A and implementation item B that needs A's output: both start in round 1
        self.world()
        self.add(item("CMD-A1"), item("CMD-B1", goal="implement against the contract of CMD-A1"))
        started = self.round()["started"]
        self.assertEqual(sorted(s["item"] for s in started), ["CMD-A1", "CMD-B1"])

    def test_R3_no_file_ownership_field(self):
        self.world()
        ok, why = self.pool().add(item("CMD-C1", files=["web/src/**"]))
        self.assertFalse(ok); self.assertIn("files", why)

    def test_R4_turn_cwd_is_node_dir_not_a_worktree(self):
        w = self.world(); seen = []
        fb = w.backends["fake_text"]; orig = fb.create
        fb.create = lambda m, o, ctx: (seen.append(ctx), orig(m, o, ctx))[1]
        self.add(item("CMD-D1"))
        for _ in range(3):
            self.round()
        self.assertTrue(seen)
        for ctx in seen:
            self.assertIn("/nodes/", ctx["cwd"].replace("\\", "/"))
            self.assertNotIn("worktree", ctx["cwd"])

    def test_R5_claude_cli_default_has_no_tools(self):
        a = ClaudeRunner(["claude"], "claude-haiku-4-5").argv("p", "sys")
        self.assertIn("--tools", a); self.assertEqual(a[a.index("--tools") + 1], "")
        b = ClaudeRunner(["claude"], "claude-haiku-4-5", bare=False).argv("p")
        self.assertFalse(any(x.startswith("--permission-mode") or x == "--allowedTools" for x in b))

    def test_R6_judge_parses_only_python_runners(self):
        vitest = " Test Files  3 passed (3)\n      Tests  12 passed (12)\n   Duration  1.2s"
        jest = "Tests:       1 failed, 11 passed, 12 total\nTime:        2.3 s"
        pw = "  12 passed (4.1s)"
        for out in (vitest, jest, pw):
            self.assertIsNone(J.parse_counts(out))

    def test_R7_judge_needs_a_pip_dist(self):
        import tempfile, json
        d = Path(tempfile.mkdtemp()); (d / ".ga-judge.json").write_text(json.dumps({"test": ["npm", "test"]}))
        with self.assertRaises(J.JudgeError):
            J.load_config(d, None)

    def test_R8_item_id_form(self):
        self.world()
        ok, why = self.pool().add(item("W-FE-01"))
        self.assertFalse(ok)

    def test_R9_l0_has_no_turn_start(self):
        src = Path("/home/user/ga-sdk/ga/net/node.py").read_text() + Path("/home/user/ga-sdk/ga/net/pool.py").read_text()
        self.assertNotIn("turn.started", src)


if __name__ == "__main__":
    unittest.main(verbosity=2)
