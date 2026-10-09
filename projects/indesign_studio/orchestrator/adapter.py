import json
import uuid

class MockAdapter:
    def __init__(self):
        self.frames = []
        self.doc_revision = 0
        self.should_fail_network = False

    def create_text_frame(self, bounds, text, style=None):
        if self.should_fail_network:
            raise ConnectionError("Network failure")
        frame_id = str(uuid.uuid4())
        # mock overflow if text is very long (dummy condition)
        overflows = len(text) > 50
        self.frames.append({
            "id": frame_id,
            "bounds": bounds,
            "text": text,
            "style": style,
            "overflows": overflows
        })
        self.doc_revision += 1
        return frame_id

    def inspect(self):
        if self.should_fail_network:
            raise ConnectionError("Network failure")
        
        report = {
            "structural_findings": [],
            "visual_findings": []
        }
        for f in self.frames:
            if f.get("overflows"):
                report["structural_findings"].append({
                    "id": str(uuid.uuid4()),
                    "op_id": "none",
                    "item_id": f["id"],
                    "severity": "error",
                    "evidence": "Text overflows frame"
                })
        return report
