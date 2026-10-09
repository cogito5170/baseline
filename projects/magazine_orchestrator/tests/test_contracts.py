"""M1 gate: contract files and magorch.contracts."""
import copy
import json
import unittest

from _helpers import CONTRACTS, EXAMPLES, NOTE_SCHEMA, example

from jsonschema import Draft202012Validator

CORE = ["magazine_project", "creative_brief", "style_specification", "design_system", "editorial_plan", "agent_task",
        "agent_result", "artifact_manifest", "qa_report", "publication_manifest", "orchestration_plan"]


class SchemaFiles(unittest.TestCase):
    def test_every_core_schema_exists_and_is_valid_2020_12(self):
        for name in CORE + ["common"]:
            path = CONTRACTS / f"{name}.schema.json"
            self.assertTrue(path.exists(), path)
            schema = json.loads(path.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
            self.assertTrue(schema["$id"].startswith(f"urn:magorch:{name}:"), schema["$id"])

    def test_every_core_contract_has_an_example(self):
        for name in CORE:
            self.assertTrue((EXAMPLES / f"{name}.json").exists(), name)


class Validate(unittest.TestCase):
    def setUp(self):
        from magorch import contracts
        self.c = contracts

    def test_examples_validate_by_their_schema_field(self):
        for name in CORE:
            self.c.validate(example(name))  # must not raise

    def test_all_core_names_registered(self):
        names = set(self.c.names())
        for name in CORE:
            self.assertIn(f"{name}/1", names)

    def _bad(self, doc, schema=None):
        with self.assertRaises(self.c.ContractError) as cm:
            self.c.validate(doc, schema)
        self.assertTrue(cm.exception.errors, "ContractError.errors must list the problems")
        self.assertIsInstance(cm.exception, ValueError)
        return cm.exception.errors

    def test_errors_carry_json_paths(self):
        t = example("agent_task")
        t["constraints"]["max_attempts"] = 0
        errs = self._bad(t)
        self.assertTrue(any(e.startswith("$.constraints.max_attempts") for e in errs), errs)

    def test_unknown_or_missing_schema_name(self):
        self._bad({"schema": "nope/9"})
        self._bad({"no": "schema"})

    def test_task_needs_acceptance_criteria(self):
        t = example("agent_task")
        t["acceptance_criteria"] = []
        self._bad(t)
        del t["acceptance_criteria"]
        self._bad(t)

    def test_task_input_ref_must_use_artifact_id_pattern(self):
        t = example("agent_task")
        t["inputs"][0]["artifact_id"] = "brief-1"
        self._bad(t)

    def test_style_confidence_needs_method_and_range(self):
        s = example("style_specification")
        s["classification"]["confidence"] = 0.88
        self._bad(s)  # confidence without confidence_method
        s["classification"]["confidence_method"] = "share of 5 classifier runs agreeing on the archetype"
        self.c.validate(s)
        s["classification"]["confidence"] = 1.5
        self._bad(s)

    def test_style_attributes_are_independent_and_required(self):
        s = example("style_specification")
        for key in ["mood", "layout", "typography", "color", "imagery", "information_density", "motifs"]:
            broken = copy.deepcopy(s)
            del broken["visual_attributes"][key]
            self._bad(broken)

    def test_qa_blocking_finding_must_be_traceable(self):
        q = example("qa_report")
        for key in ["affected_artifact_id", "recommended_agent", "recommended_action", "evidence"]:
            broken = copy.deepcopy(q)
            del broken["checks"][1][key]
            self._bad(broken)

    def test_qa_cannot_approve_with_blocking_issues(self):
        q = example("qa_report")
        q["publication_decision"] = "approved"
        self._bad(q)
        q["status"] = "passed"
        self._bad(q)  # summary still has 1 blocking issue

    def test_completed_result_cannot_carry_failed_output_validation(self):
        r = example("agent_result")
        r["outputs"][0]["validation_status"] = "failed"
        self._bad(r)

    def test_failed_result_needs_reason(self):
        r = example("agent_result")
        r["status"] = "failed"
        self._bad(r)
        r["failure_reason"] = "agent raised RuntimeError"
        self.c.validate(r)

    def test_creative_article_needs_fiction_label(self):
        e = example("editorial_plan")
        e["articles"][2]["fiction_label"] = None
        self._bad(e)

    def test_published_manifest_needs_approved_qa(self):
        p = example("publication_manifest")
        p["qa_report"]["publication_decision"] = "blocked"
        self._bad(p)

    def test_register_extra_contract(self):
        if "test_note/1" not in self.c.names():
            self.c.register("test_note/1", NOTE_SCHEMA)
        self.c.validate({"schema": "test_note/1", "text": "x"})
        self._bad({"schema": "test_note/1", "text": ""})
        other = copy.deepcopy(NOTE_SCHEMA)
        other["required"] = ["schema"]
        with self.assertRaises(self.c.ContractError):
            self.c.register("test_note/1", other)

    def test_explicit_schema_argument_wins(self):
        brief = example("creative_brief")
        with self.assertRaises(self.c.ContractError):
            self.c.validate(brief, "style_specification/1")


if __name__ == "__main__":
    unittest.main()
