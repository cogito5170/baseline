"""M1 gate: retries, repair of invalid output, timeouts, blocking, cancellation, agent isolation."""
import tempfile
import time
import unittest
from pathlib import Path

from _helpers import Recorder, register_note, task


class Failures(unittest.TestCase):
    def setUp(self):
        register_note()
        from magorch.contracts import validate
        from magorch.engine import Engine
        self.Engine, self.validate = Engine, validate
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.rec = Recorder()

    def tearDown(self):
        self.tmp.cleanup()

    def test_exception_is_retried_then_succeeds(self):
        e = self.Engine(self.dir, {"editorial_director": self.rec.agent(fail_times=1)})
        e.add_task(task("TASK-A", "editorial_director", max_attempts=3))
        self.assertEqual(e.run()["TASK-A"], "succeeded")
        self.assertEqual([c["task"]["attempt"] for c in self.rec.calls_for("TASK-A")], [1, 2])
        self.assertEqual(e.result("TASK-A")["provenance"]["attempts"], 2)
        self.assertIn("task_retry", [ev["event"] for ev in e.events()])

    def test_exhausted_attempts_fail_and_block_dependents(self):
        e = self.Engine(self.dir, {"editorial_director": self.rec.agent(fail_times=99),
                                   "article_writer_editor": self.rec.agent()})
        e.add_task(task("TASK-A", "editorial_director", max_attempts=2))
        e.add_task(task("TASK-B", "article_writer_editor", deps=["TASK-A"], inputs=["ART-A"]))
        e.add_task(task("TASK-C", "article_writer_editor", deps=["TASK-B"], inputs=["ART-B"]))
        statuses = e.run()
        self.assertEqual(statuses, {"TASK-A": "failed", "TASK-B": "blocked", "TASK-C": "blocked"})
        self.assertEqual(len(self.rec.calls_for("TASK-A")), 2)
        self.assertEqual(self.rec.calls_for("TASK-B") + self.rec.calls_for("TASK-C"), [])
        r = e.result("TASK-A")
        self.validate(r)
        self.assertEqual(r["status"], "failed")
        self.assertEqual(r["outputs"], [])
        self.assertIn("RuntimeError", r["failure_reason"])
        self.assertIsNone(e.store.latest_version("ART-A"))

    def test_invalid_output_is_rejected_and_repaired(self):
        e = self.Engine(self.dir, {"editorial_director": self.rec.agent(bad_times=1)})
        e.add_task(task("TASK-A", "editorial_director", max_attempts=3))
        self.assertEqual(e.run()["TASK-A"], "succeeded")
        calls = self.rec.calls_for("TASK-A")
        self.assertEqual(len(calls), 2)
        self.assertNotIn("repair_context", calls[0]["task"])
        errors = calls[1]["task"]["repair_context"]["errors"]
        self.assertTrue(any("$.text" in err for err in errors), errors)
        self.assertEqual(e.store.latest_version("ART-A"), 1, "the invalid attempt stored nothing")
        self.assertEqual(e.result("TASK-A")["outputs"][0]["validation_status"], "passed")

    def test_invalid_output_every_time_ends_failed(self):
        e = self.Engine(self.dir, {"editorial_director": self.rec.agent(bad_times=99)})
        e.add_task(task("TASK-A", "editorial_director", max_attempts=2))
        self.assertEqual(e.run()["TASK-A"], "failed")
        r = e.result("TASK-A")
        self.assertIn(r["status"], ("failed", "invalid_output"))
        self.assertTrue(r["validation_errors"])
        self.assertIsNone(e.store.latest_version("ART-A"))

    def test_timeout_does_not_hang_and_late_result_is_discarded(self):
        e = self.Engine(self.dir, {"editorial_director": self.rec.agent(sleep=0.8)})
        e.add_task(task("TASK-A", "editorial_director", max_attempts=2, timeout=0.2))
        t0 = time.monotonic()
        self.assertEqual(e.run()["TASK-A"], "timed_out")
        self.assertLess(time.monotonic() - t0, 1.5, "run() waited for a timed-out agent")
        time.sleep(1.2)  # let the abandoned agent threads return
        self.assertIsNone(e.store.latest_version("ART-A"), "a late result must never be stored")
        self.assertEqual(e.status("TASK-A"), "timed_out")
        self.assertIn("task_timed_out", [ev["event"] for ev in e.events()])

    def test_cancel_before_run_blocks_dependents(self):
        e = self.Engine(self.dir, {"editorial_director": self.rec.agent(), "article_writer_editor": self.rec.agent()})
        e.add_task(task("TASK-A", "editorial_director"))
        e.add_task(task("TASK-B", "article_writer_editor", deps=["TASK-A"], inputs=["ART-A"]))
        e.add_task(task("TASK-X", "article_writer_editor"))
        e.cancel("TASK-A")
        statuses = e.run()
        self.assertEqual(statuses["TASK-A"], "cancelled")
        self.assertEqual(statuses["TASK-B"], "blocked")
        self.assertEqual(statuses["TASK-X"], "succeeded", "unrelated work continues")
        self.assertEqual(self.rec.calls_for("TASK-A") + self.rec.calls_for("TASK-B"), [])

    def test_agent_cannot_mutate_canonical_inputs(self):
        e = self.Engine(self.dir, {"editorial_director": self.rec.agent(),
                                   "article_writer_editor": self.rec.agent(mutate_inputs=True)})
        e.add_task(task("TASK-A", "editorial_director", out_ids=["ART-A"]))
        e.add_task(task("TASK-B", "article_writer_editor", deps=["TASK-A"], inputs=["ART-A"]))
        e.run()
        self.assertNotEqual(e.store.get("ART-A")["text"], "MUTATED BY AGENT")

    def test_missing_agent_role_fails_task(self):
        e = self.Engine(self.dir, {})
        e.add_task(task("TASK-A", "editorial_director"))
        self.assertEqual(e.run()["TASK-A"], "failed")
        self.assertIn("editorial_director", e.result("TASK-A")["failure_reason"])


if __name__ == "__main__":
    unittest.main()
