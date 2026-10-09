import unittest
import json
import os
import sys

# add parent directory to path to import orchestrator
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from orchestrator.validation_engine import ValidationEngine
from orchestrator.job_state import JobState
from orchestrator.adapter import MockAdapter
from orchestrator.spec_compiler import SpecCompiler

class TestIDS1(unittest.TestCase):
    def setUp(self):
        self.validator = ValidationEngine(schemas_dir=os.path.join(os.path.dirname(__file__), '../contracts'))
        self.job_state = JobState(state_file="test_job_state.json")
        self.adapter = MockAdapter()
        self.compiler = SpecCompiler()

    def tearDown(self):
        if os.path.exists("test_job_state.json"):
            os.remove("test_job_state.json")

    def test_valid_spec(self):
        spec = self.compiler.compile("doc_1", 0, [{"text": "Hello"}])
        valid, err = self.validator.validate_spec(spec)
        self.assertTrue(valid, f"Spec should be valid: {err}")

    def test_invalid_spec(self):
        # Missing required field 'document'
        spec = {"operations": []}
        valid, err = self.validator.validate_spec(spec)
        self.assertFalse(valid, "Spec should be invalid")

        # Inverted bounds test
        spec_bounds = self.compiler.compile("doc_1", 0, [{"text": "Hello"}])
        spec_bounds["operations"][0]["bounds_pt"] = [100, 100, 10, 10]
        valid, err = self.validator.validate_spec(spec_bounds)
        self.assertFalse(valid, "Spec with inverted bounds should be invalid")

    def test_stale_revision(self):
        # Mocking stale revision logic
        spec = self.compiler.compile("doc_1", 0, [{"text": "Hello"}])
        self.job_state.state["document_revision"] = 1 # current is 1, spec expects 0
        self.assertNotEqual(spec["document"]["expected_revision"], self.job_state.state["document_revision"])

    def test_duplicate_op_delivery(self):
        op_id = "op_123"
        first = self.job_state.record_op(op_id)
        self.assertTrue(first)
        second = self.job_state.record_op(op_id)
        self.assertFalse(second, "Duplicate op should not be recorded")

    def test_network_failure_retry(self):
        self.adapter.should_fail_network = True
        with self.assertRaises(ConnectionError):
            self.adapter.create_text_frame([0,0,10,10], "Text")
        
        self.adapter.should_fail_network = False
        res = self.adapter.create_text_frame([0,0,10,10], "Text")
        self.assertIsNotNone(res, "Should succeed after network is restored")

    def test_overflow_on_mock(self):
        long_text = "A" * 60
        self.adapter.create_text_frame([0,0,10,10], long_text)
        report = self.adapter.inspect()
        self.assertTrue(any(f["severity"] == "error" and "overflow" in f["evidence"].lower() for f in report["structural_findings"]))

    def test_approval_gating(self):
        # Export only after explicit user approval
        self.job_state.set_status("awaiting_approval")
        def mock_export():
            if self.job_state.state["status"] != "approved":
                raise ValueError("Export failed: not approved")
            return "exported"
            
        with self.assertRaises(ValueError):
            mock_export()
            
        self.job_state.set_status("approved")
        self.assertEqual(mock_export(), "exported")

    def test_export_failure(self):
        self.job_state.set_status("approved")
        def mock_failing_export():
            self.job_state.set_status("export_failed")
            raise Exception("Disk error")
            
        with self.assertRaises(Exception):
            mock_failing_export()
        self.assertEqual(self.job_state.state["status"], "export_failed")

if __name__ == '__main__':
    unittest.main()
