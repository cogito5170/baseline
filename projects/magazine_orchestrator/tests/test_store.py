"""M1 gate: magorch.store.ArtifactStore."""
import hashlib
import tempfile
import unittest
from pathlib import Path

from _helpers import example, register_note


class Store(unittest.TestCase):
    def setUp(self):
        register_note()
        from magorch.contracts import ContractError, validate
        from magorch.store import ArtifactStore
        self.ContractError, self.validate, self.ArtifactStore = ContractError, validate, ArtifactStore
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "artifacts"
        self.s = ArtifactStore(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def note(self, text="hello"):
        return {"schema": "test_note/1", "text": text}

    def test_versions_increment_and_are_immutable(self):
        r1 = self.s.put("ART-N", "note", self.note("one"), produced_by="TASK-A")
        r2 = self.s.put("ART-N", "note", self.note("two"), produced_by="TASK-A")
        self.assertEqual(r1, {"artifact_id": "ART-N", "version": 1})
        self.assertEqual(r2["version"], 2)
        self.assertEqual(self.s.get("ART-N", 1)["text"], "one")
        self.assertEqual(self.s.get("ART-N")["text"], "two")
        self.assertEqual(self.s.latest_version("ART-N"), 2)
        self.assertIsNone(self.s.latest_version("ART-NONE"))
        with self.assertRaises(KeyError):
            self.s.get("ART-NONE")

    def test_get_returns_a_copy(self):
        self.s.put("ART-N", "note", self.note("keep"), produced_by="TASK-A")
        got = self.s.get("ART-N")
        got["text"] = "changed"
        self.assertEqual(self.s.get("ART-N")["text"], "keep")

    def test_put_does_not_alias_the_callers_dict(self):
        payload = self.note("orig")
        self.s.put("ART-N", "note", payload, produced_by="TASK-A")
        payload["text"] = "changed after put"
        self.assertEqual(self.s.get("ART-N")["text"], "orig")

    def test_invalid_payload_stores_nothing(self):
        with self.assertRaises(self.ContractError):
            self.s.put("ART-N", "note", self.note(""), produced_by="TASK-A")
        self.assertIsNone(self.s.latest_version("ART-N"))

    def test_payload_id_and_version_must_match(self):
        style = example("style_specification")  # artifact_id ART-STYLE-001, version 1
        self.s.put("ART-STYLE-001", "style_specification", style, produced_by="TASK-STYLE-001")
        with self.assertRaises((self.ContractError, ValueError)):
            self.s.put("ART-STYLE-001", "style_specification", style, produced_by="TASK-STYLE-001")  # says v1, gets v2
        self.assertEqual(self.s.latest_version("ART-STYLE-001"), 1)

    def test_persistence_across_instances(self):
        self.s.put("ART-N", "note", self.note("persist"), produced_by="TASK-A",
                   inputs=[{"artifact_id": "ART-IN", "version": 3}])
        again = self.ArtifactStore(self.root)
        self.assertEqual(again.get("ART-N")["text"], "persist")
        self.assertEqual(again.record("ART-N", 1)["inputs"], [{"artifact_id": "ART-IN", "version": 3}])

    def test_record_hash_matches_stored_file(self):
        self.s.put("ART-N", "note", self.note("hash me"), produced_by="TASK-A")
        rec = self.s.record("ART-N", 1)
        path = self.root.parent / rec["path"]
        self.assertTrue(path.exists(), path)
        self.assertEqual(rec["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(rec["produced_by"], "TASK-A")
        self.assertEqual(rec["validation_status"], "passed")

    def test_bytes_payload(self):
        data = b"%PDF-1.7 fake"
        with self.assertRaises((TypeError, ValueError)):
            self.s.put("ART-PDF", "rendered_pdf", data, produced_by="TASK-R", media_type=None)
        self.s.put("ART-PDF", "rendered_pdf", data, produced_by="TASK-R", media_type="application/pdf")
        self.assertEqual(self.s.get("ART-PDF"), data)
        rec = self.s.record("ART-PDF", 1)
        self.assertEqual(rec["validation_status"], "not_applicable")
        self.assertEqual(rec["sha256"], hashlib.sha256(data).hexdigest())

    def test_approval_is_separate_from_payload(self):
        self.s.put("ART-N", "note", self.note("x"), produced_by="TASK-A")
        before = self.s.record("ART-N", 1)["sha256"]
        self.assertEqual(self.s.approval_status("ART-N", 1), "pending")
        self.s.approve("ART-N", 1, by="user")
        self.assertEqual(self.s.approval_status("ART-N", 1), "approved")
        self.assertEqual(self.s.record("ART-N", 1)["sha256"], before)
        self.s.put("ART-N", "note", self.note("y"), produced_by="TASK-A")
        self.assertEqual(self.s.approval_status("ART-N", 2), "pending", "a new version is never pre-approved")
        self.s.reject("ART-N", 2, by="user", note="tone is off")
        self.assertEqual(self.s.approval_status("ART-N", 2), "rejected")
        self.s.put("ART-M", "note", self.note("z"), produced_by="TASK-A", approval_required=False)
        self.assertEqual(self.s.approval_status("ART-M", 1), "not_required")

    def test_manifest_is_a_valid_contract(self):
        self.s.put("ART-N", "note", self.note("a"), produced_by="TASK-A")
        self.s.put("ART-N", "note", self.note("b"), produced_by="orchestrator:revision")
        self.s.put("ART-PDF", "rendered_pdf", b"x", produced_by="TASK-R", media_type="application/pdf")
        m = self.s.manifest("MAG-2026-901")
        self.validate(m)
        self.assertEqual(sorted((a["artifact_id"], a["version"]) for a in m["artifacts"]),
                         [("ART-N", 1), ("ART-N", 2), ("ART-PDF", 1)])


if __name__ == "__main__":
    unittest.main()
