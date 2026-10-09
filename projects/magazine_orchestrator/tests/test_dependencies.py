"""M1 gate: dependency graph, scheduling order, input binding, concurrency."""
import tempfile
import time
import unittest
from pathlib import Path

from _helpers import Recorder, register_note, task


class Graph(unittest.TestCase):
    def test_topological_order_is_deterministic(self):
        from magorch.graph import topological_order
        edges = {"D": ["B", "C"], "B": ["A"], "C": ["A"], "A": []}
        self.assertEqual(topological_order(edges), ["A", "B", "C", "D"])

    def test_cycle_is_named(self):
        from magorch.graph import PlanError, topological_order
        with self.assertRaises(PlanError) as cm:
            topological_order({"A": ["C"], "B": ["A"], "C": ["B"]})
        for node in "ABC":
            self.assertIn(node, str(cm.exception))

    def test_descendants(self):
        from magorch.graph import descendants
        edges = {"D": ["B", "C"], "B": ["A"], "C": ["A"], "A": [], "E": []}
        self.assertEqual(descendants(edges, "A"), {"B", "C", "D"})
        self.assertEqual(descendants(edges, "E"), set())


class Scheduling(unittest.TestCase):
    def setUp(self):
        register_note()
        from magorch.engine import Engine
        from magorch.graph import PlanError
        self.Engine, self.PlanError = Engine, PlanError
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.rec = Recorder()

    def tearDown(self):
        self.tmp.cleanup()

    def engine(self, agents=None, **kw):
        return self.Engine(self.dir, agents or {r: self.rec.agent() for r in
                                                ["creative_brief_analyst", "editorial_director", "style_taxonomist",
                                                 "design_system_architect", "article_writer_editor",
                                                 "layout_composer"]}, **kw)

    def test_default_graph_runs_in_dependency_order_and_binds_inputs(self):
        e = self.engine()
        e.add_task(task("TASK-BRIEF", "creative_brief_analyst"))
        e.add_task(task("TASK-EDIT", "editorial_director", deps=["TASK-BRIEF"], inputs=["ART-BRIEF"]))
        e.add_task(task("TASK-STYLE", "style_taxonomist", deps=["TASK-BRIEF"], inputs=["ART-BRIEF"]))
        e.add_task(task("TASK-DESIGN", "design_system_architect", deps=["TASK-STYLE"], inputs=["ART-STYLE"]))
        e.add_task(task("TASK-WRITE", "article_writer_editor", deps=["TASK-EDIT", "TASK-DESIGN"],
                        inputs=["ART-EDIT", "ART-DESIGN"]))
        e.add_task(task("TASK-LAYOUT", "layout_composer", deps=["TASK-WRITE", "TASK-DESIGN"],
                        inputs=["ART-WRITE", "ART-DESIGN"]))
        statuses = e.run()
        self.assertEqual(set(statuses.values()), {"succeeded"}, statuses)
        ends = {c["task_id"]: c["end"] for c in self.rec.calls}
        starts = {c["task_id"]: c["start"] for c in self.rec.calls}
        for child, parents in {"TASK-EDIT": ["TASK-BRIEF"], "TASK-STYLE": ["TASK-BRIEF"],
                               "TASK-DESIGN": ["TASK-STYLE"], "TASK-WRITE": ["TASK-EDIT", "TASK-DESIGN"],
                               "TASK-LAYOUT": ["TASK-WRITE", "TASK-DESIGN"]}.items():
            for p in parents:
                self.assertGreaterEqual(starts[child], ends[p], f"{child} started before {p} finished")
        call = self.rec.calls_for("TASK-LAYOUT")[0]
        self.assertEqual(sorted(call["inputs"]), ["ART-DESIGN", "ART-WRITE"])
        self.assertEqual({i["artifact_id"]: i["version"] for i in call["task"]["inputs"]},
                         {"ART-WRITE": 1, "ART-DESIGN": 1}, "inputs are bound to concrete versions at dispatch")
        result = e.result("TASK-LAYOUT")
        self.assertEqual(sorted((i["artifact_id"], i["version"]) for i in result["provenance"]["input_versions"]),
                         [("ART-DESIGN", 1), ("ART-WRITE", 1)])

    def test_dispatched_tasks_are_valid(self):
        from magorch.contracts import validate
        e = self.engine()
        e.add_task(task("TASK-BRIEF", "creative_brief_analyst"))
        e.add_task(task("TASK-EDIT", "editorial_director", deps=["TASK-BRIEF"], inputs=["ART-BRIEF"]))
        e.run()
        for c in self.rec.calls:
            validate(c["task"])
            self.assertEqual(c["task"]["status"], "running")
            self.assertEqual(c["task"]["attempt"], 1)
        for tid in ["TASK-BRIEF", "TASK-EDIT"]:
            validate(e.result(tid))

    def test_invalid_task_is_rejected_at_submission(self):
        from magorch.contracts import ContractError
        e = self.engine()
        bad = task("TASK-X", "editorial_director")
        bad["acceptance_criteria"] = []
        with self.assertRaises(ContractError):
            e.add_task(bad)
        bad = task("TASK-X", "not_a_role")
        with self.assertRaises(ContractError):
            e.add_task(bad)

    def test_unknown_dependency_and_cycle(self):
        e = self.engine()
        e.add_task(task("TASK-A", "editorial_director", deps=["TASK-GHOST"]))
        with self.assertRaises(self.PlanError):
            e.run()
        e2 = self.Engine(self.dir / "p2", {"editorial_director": self.rec.agent()})
        e2.add_task(task("TASK-A", "editorial_director", deps=["TASK-B"]))
        with self.assertRaises(self.PlanError):
            e2.add_task(task("TASK-B", "editorial_director", deps=["TASK-A"]))

    def test_missing_input_artifact_fails_without_retry(self):
        e = self.engine()
        e.add_task(task("TASK-A", "editorial_director", inputs=["ART-NEVER-MADE"], max_attempts=3))
        self.assertEqual(e.run()["TASK-A"], "failed")
        self.assertEqual(self.rec.calls_for("TASK-A"), [])
        self.assertTrue(e.result("TASK-A")["failure_reason"].startswith("missing_input"))

    def test_output_ids_must_match_contract(self):
        e = self.engine({"editorial_director": self.rec.agent(out_for={"TASK-A": ["ART-WRONG"]})})
        e.add_task(task("TASK-A", "editorial_director", out_ids=["ART-RIGHT"], max_attempts=2))
        self.assertEqual(e.run()["TASK-A"], "failed")
        self.assertIsNone(e.store.latest_version("ART-WRONG"))
        self.assertEqual(len(self.rec.calls_for("TASK-A")), 2)

    def test_parallel_independent_tasks_overlap(self):
        e = self.engine({"article_writer_editor": self.rec.agent(sleep=0.4)}, max_concurrent=4)
        for i in range(4):
            e.add_task(task(f"TASK-W{i}", "article_writer_editor"))
        t0 = time.monotonic()
        e.run()
        elapsed = time.monotonic() - t0
        self.assertGreaterEqual(self.rec.max_active, 2, "independent tasks must run concurrently")
        self.assertLess(elapsed, 1.4, f"4 x 0.4 s tasks took {elapsed:.2f} s; not concurrent")

    def test_parallel_respects_max_concurrent(self):
        e = self.engine({"article_writer_editor": self.rec.agent(sleep=0.15)}, max_concurrent=2)
        for i in range(6):
            e.add_task(task(f"TASK-W{i}", "article_writer_editor"))
        statuses = e.run()
        self.assertEqual(set(statuses.values()), {"succeeded"})
        self.assertLessEqual(self.rec.max_active, 2)
        self.assertEqual(self.rec.max_active, 2)

    def test_succeeded_task_is_not_rerun(self):
        e = self.engine()
        e.add_task(task("TASK-A", "editorial_director"))
        e.run()
        e.add_task(task("TASK-A", "editorial_director"))  # identical: no-op
        e.run()
        self.assertEqual(len(self.rec.calls_for("TASK-A")), 1)
        from magorch.contracts import ContractError
        with self.assertRaises(ContractError):
            e.add_task(task("TASK-A", "editorial_director", objective="something else"))

    def test_state_survives_a_new_engine(self):
        e = self.engine()
        e.add_task(task("TASK-A", "editorial_director"))
        e.add_task(task("TASK-B", "style_taxonomist", deps=["TASK-A"], inputs=["ART-A"]))
        e.run()
        again = self.engine()
        self.assertEqual(again.status("TASK-B"), "succeeded")
        self.assertEqual(again.result("TASK-B")["outputs"][0]["artifact_id"], "ART-B")
        again.run()
        self.assertEqual(len(self.rec.calls), 2, "a restored engine must not re-run finished work")

    def test_events_are_logged(self):
        e = self.engine()
        e.add_task(task("TASK-A", "editorial_director"))
        e.run()
        names = [ev["event"] for ev in e.events()]
        for name in ["task_added", "task_dispatched", "artifact_stored", "task_succeeded"]:
            self.assertIn(name, names)
        self.assertTrue((self.dir / "events.jsonl").exists())
        self.assertTrue(all("ts" in ev for ev in e.events()))


if __name__ == "__main__":
    unittest.main()
