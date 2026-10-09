"""M1 gate: revision propagation (wave rule), revalidation, QA finding routing, revision limit."""
import copy
import tempfile
import unittest
from pathlib import Path

from _helpers import Recorder, example, register_note, task


class Revisions(unittest.TestCase):
    def setUp(self):
        register_note()
        from magorch.engine import Engine
        self.Engine = Engine
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.rec = Recorder()
        self.validator_calls = []

    def tearDown(self):
        self.tmp.cleanup()

    def build(self, verdict=()):
        """design -> article (revalidate) -> layout (rerun) -> qa ; plus an unrelated research task."""
        def article_validator(task_doc, inputs, previous_result):
            self.validator_calls.append({"task": task_doc, "inputs": inputs, "previous": previous_result})
            return list(verdict)

        roles = ["design_system_architect", "article_writer_editor", "layout_composer", "quality_assurance_editor",
                 "research_fact_checker"]
        e = self.Engine(self.dir, {r: self.rec.agent() for r in roles},
                        validators={"article_writer_editor": article_validator})
        e.add_task(task("TASK-DESIGN", "design_system_architect"))
        e.add_task(task("TASK-RESEARCH", "research_fact_checker"))
        e.add_task(task("TASK-WRITE", "article_writer_editor", deps=["TASK-DESIGN", "TASK-RESEARCH"],
                        inputs=["ART-DESIGN", "ART-RESEARCH"], on_change="revalidate"))
        e.add_task(task("TASK-LAYOUT", "layout_composer", deps=["TASK-DESIGN", "TASK-WRITE"],
                        inputs=["ART-DESIGN", "ART-WRITE"]))
        e.add_task(task("TASK-QA", "quality_assurance_editor", deps=["TASK-LAYOUT"], inputs=["ART-LAYOUT"]))
        self.assertEqual(set(e.run().values()), {"succeeded"})
        return e

    def count(self, tid):
        return len(self.rec.calls_for(tid))

    def test_design_token_update_revalidates_articles_and_reruns_layout(self):
        e = self.build(verdict=())
        new = {"schema": "test_note/1", "text": "accent #FF5A36"}
        ref = e.revise_artifact("ART-DESIGN", new, artifact_type="note", reason="user changed accent token")
        self.assertEqual(ref, {"artifact_id": "ART-DESIGN", "version": 2})
        self.assertEqual(e.status("TASK-WRITE"), "stale")
        self.assertEqual(e.status("TASK-LAYOUT"), "stale")
        self.assertEqual(e.status("TASK-RESEARCH"), "succeeded")
        statuses = e.run()
        self.assertEqual(set(statuses.values()), {"succeeded"}, statuses)
        self.assertEqual(self.count("TASK-WRITE"), 1, "revalidate policy: the article agent is not called again")
        self.assertEqual(len(self.validator_calls), 1)
        self.assertEqual(self.validator_calls[0]["inputs"]["ART-DESIGN"]["text"], "accent #FF5A36")
        self.assertEqual(e.store.latest_version("ART-WRITE"), 1, "revalidation creates no new article version")
        write_inputs = {i["artifact_id"]: i["version"] for i in e.result("TASK-WRITE")["provenance"]["input_versions"]}
        self.assertEqual(write_inputs["ART-DESIGN"], 2)
        self.assertEqual(self.count("TASK-LAYOUT"), 2)
        self.assertEqual(self.count("TASK-QA"), 2, "layout produced v2, so QA re-inspects")
        self.assertEqual(self.count("TASK-RESEARCH"), 1)
        self.assertEqual(self.count("TASK-DESIGN"), 1, "a revised artifact does not re-run its original producer")
        names = [ev["event"] for ev in e.events()]
        for n in ["artifact_revised", "task_stale", "task_revalidated"]:
            self.assertIn(n, names)
        self.assertEqual(e.store.record("ART-DESIGN", 2)["produced_by"], "orchestrator:revision")

    def test_failed_revalidation_reruns_with_messages(self):
        e = self.build(verdict=("article exceeds the new template capacity by 120 chars",))
        e.revise_artifact("ART-DESIGN", {"schema": "test_note/1", "text": "smaller body"}, artifact_type="note",
                          reason="smaller page")
        e.run()
        calls = self.rec.calls_for("TASK-WRITE")
        self.assertEqual(len(calls), 2)
        self.assertIn("article exceeds the new template capacity by 120 chars",
                      calls[1]["task"]["repair_context"]["errors"])
        self.assertEqual(e.store.latest_version("ART-WRITE"), 2)

    def test_unchanged_artifact_does_not_wake_consumers(self):
        e = self.build()
        e.revise_artifact("ART-RESEARCH", {"schema": "test_note/1", "text": "new source"}, artifact_type="note",
                          reason="added a source")
        self.assertEqual(e.status("TASK-WRITE"), "stale")
        self.assertEqual(e.status("TASK-LAYOUT"), "succeeded", "only direct consumers become stale at first")
        e.run()
        self.assertEqual(self.count("TASK-LAYOUT"), 1, "article revalidated without a new version -> layout untouched")

    def finding(self, report_id, artifact_id, agent="layout_composer"):
        q = example("qa_report")
        q["report_id"] = report_id
        q["project_id"] = "MAG-2026-901"
        q["checks"][1]["affected_artifact_id"] = artifact_id
        q["checks"][1]["recommended_agent"] = agent
        return q

    def test_route_findings_reruns_only_affected_branch(self):
        e = self.build()
        routed = e.route_findings(self.finding("QA-001", "ART-LAYOUT"))
        self.assertEqual(routed, ["TASK-LAYOUT"])
        self.assertEqual(e.status("TASK-LAYOUT"), "stale")
        self.assertEqual(e.status("TASK-WRITE"), "succeeded")
        e.run()
        calls = self.rec.calls_for("TASK-LAYOUT")
        self.assertEqual(len(calls), 2)
        notes = calls[1]["task"]["revision_notes"]
        self.assertEqual(notes[0]["finding_id"], "QA-LAYOUT-001")
        self.assertEqual(notes[0]["report_id"], "QA-001")
        self.assertIn("7페이지", notes[0]["message"])
        self.assertEqual(self.count("TASK-WRITE"), 1)
        self.assertEqual(self.count("TASK-DESIGN"), 1)
        self.assertEqual(self.count("TASK-QA"), 2)
        self.assertIn("finding_routed", [ev["event"] for ev in e.events()])

    def test_non_blocking_and_passed_checks_are_not_routed(self):
        e = self.build()
        q = self.finding("QA-002", "ART-LAYOUT")
        q["checks"][1]["severity"] = "minor"
        q["summary"] = {"blocking_issues": 0, "major_issues": 0, "minor_issues": 1}
        self.assertEqual(e.route_findings(q), [])
        self.assertEqual(e.status("TASK-LAYOUT"), "succeeded")

    def test_unknown_artifact_is_reported_unrouted(self):
        e = self.build()
        self.assertEqual(e.route_findings(self.finding("QA-003", "ART-PAGE-007")), [])
        self.assertIn("QA-LAYOUT-001", e.unrouted)

    def test_invalid_report_is_rejected(self):
        from magorch.contracts import ContractError
        e = self.build()
        q = self.finding("QA-004", "ART-LAYOUT")
        del q["checks"][1]["recommended_action"]
        with self.assertRaises(ContractError):
            e.route_findings(q)

    def test_revision_limit_escalates(self):
        e = self.build()
        # TASK-LAYOUT was created with revision_limit 2 (helper default)
        for n in (1, 2):
            self.assertEqual(e.route_findings(self.finding(f"QA-01{n}", "ART-LAYOUT")), ["TASK-LAYOUT"])
            e.run()
        self.assertEqual(e.route_findings(self.finding("QA-013", "ART-LAYOUT")), [])
        self.assertEqual(e.status("TASK-LAYOUT"), "failed")
        self.assertTrue(e.result("TASK-LAYOUT")["failure_reason"].startswith("revision_limit"))
        self.assertIn("escalated", [ev["event"] for ev in e.events()])
        self.assertEqual(self.count("TASK-LAYOUT"), 3)

    def test_upstream_reruns_do_not_count_against_revision_limit(self):
        e = self.build()
        for n in range(3):
            e.revise_artifact("ART-DESIGN", {"schema": "test_note/1", "text": f"token change {n}"},
                              artifact_type="note", reason="token")
            e.run()
        self.assertEqual(e.status("TASK-LAYOUT"), "succeeded")
        self.assertEqual(e.route_findings(self.finding("QA-021", "ART-LAYOUT")), ["TASK-LAYOUT"])


if __name__ == "__main__":
    unittest.main()
