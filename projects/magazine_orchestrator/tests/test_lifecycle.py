import unittest
from datetime import datetime, timezone
from magorch.lifecycle import advance, TransitionError, PHASES
from magorch.contracts import validate
from tests._helpers import example

class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.proj = example("magazine_project")
        self.proj["status"] = "intake"
        
    def test_brief_normalization(self):
        # allowed
        p = advance(self.proj, "brief_normalization")
        self.assertEqual(p["status"], "brief_normalization")
        
        # refused (from wrong state)
        self.proj["status"] = "style_specification"
        with self.assertRaises(TransitionError):
            advance(self.proj, "brief_normalization")
            
    def test_editorial_planning(self):
        self.proj["status"] = "brief_normalization"
        self.proj["creative_brief"].update({"approval_status": "approved"})
        p = advance(self.proj, "editorial_planning")
        
        # refused
        self.proj["creative_brief"]["approval_status"] = "pending"
        with self.assertRaises(TransitionError):
            advance(self.proj, "editorial_planning")
            
    def test_style_specification(self):
        self.proj["status"] = "editorial_planning"
        self.proj["creative_brief"].update({"approval_status": "approved"})
        p = advance(self.proj, "style_specification")
        
        self.proj["creative_brief"]["approval_status"] = "rejected"
        with self.assertRaises(TransitionError):
            advance(self.proj, "style_specification")
            
    def test_design_system(self):
        self.proj["status"] = "style_specification"
        self.proj["style_specification"].update({"approval_status": "approved"})
        p = advance(self.proj, "design_system")
        
        self.proj["style_specification"]["approval_status"] = "pending"
        with self.assertRaises(TransitionError):
            advance(self.proj, "design_system")
            
    def test_content_and_asset_production(self):
        self.proj["status"] = "design_system"
        self.proj["editorial_plan"].update({"approval_status": "approved"})
        self.proj["design_system"].update({"status": "produced"})
        p = advance(self.proj, "content_and_asset_production")
        
        self.proj["design_system"]["status"] = "pending"
        with self.assertRaises(TransitionError):
            advance(self.proj, "content_and_asset_production")
            
        self.proj["status"] = "revision"
        self.proj["design_system"]["status"] = "produced"
        advance(self.proj, "content_and_asset_production")
        
    def test_layout_assembly(self):
        self.proj["status"] = "content_and_asset_production"
        self.proj["design_system"].update({"status": "produced"})
        advance(self.proj, "layout_assembly")
        
        self.proj["design_system"]["status"] = "failed"
        with self.assertRaises(TransitionError):
            advance(self.proj, "layout_assembly")
            
    def test_qa(self):
        self.proj["status"] = "layout_assembly"
        self.proj["layout"].update({"status": "produced"})
        advance(self.proj, "qa")
        
        self.proj["layout"]["status"] = "pending"
        with self.assertRaises(TransitionError):
            advance(self.proj, "qa")
            
    def test_revision(self):
        self.proj["status"] = "qa"
        self.proj["quality"].update({"blocking_issues": 1})
        self.proj["revision_cycles"].update({"count": 0, "max": 2})
        p = advance(self.proj, "revision")
        self.assertEqual(p["revision_cycles"]["count"], 1)
        
        self.proj["revision_cycles"]["count"] = 2
        with self.assertRaises(TransitionError):
            advance(self.proj, "revision")
            
    def test_final_render(self):
        self.proj["status"] = "qa"
        self.proj["quality"].update({"blocking_issues": 0, "last_report_id": "QA1"})
        advance(self.proj, "final_render")
        
        self.proj["quality"]["blocking_issues"] = 1
        with self.assertRaises(TransitionError):
            advance(self.proj, "final_render")
            
    def test_published(self):
        self.proj["status"] = "final_render"
        self.proj["publication"].update({"status": "rendered"})
        self.proj["quality"].update({"blocking_issues": 0, "publication_approved": True, "last_report_id": "QA1"})
        advance(self.proj, "published")
        
        self.proj["publication"]["status"] = "failed"
        with self.assertRaises(TransitionError):
            advance(self.proj, "published")

    def test_failed_cancelled(self):
        self.proj["status"] = "intake"
        advance(self.proj, "failed")
        
        self.proj["status"] = "failed"
        with self.assertRaises(TransitionError):
            advance(self.proj, "cancelled")

if __name__ == "__main__":
    unittest.main()
