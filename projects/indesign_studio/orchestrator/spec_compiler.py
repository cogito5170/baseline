import uuid

class SpecCompiler:
    def __init__(self):
        pass

    def compile(self, document_id, expected_revision, instructions):
        # A simple compiler that produces a spec based on dummy instructions
        ops = []
        for i, inst in enumerate(instructions):
            ops.append({
                "op_id": str(uuid.uuid4()),
                "op": "create_text_frame",
                "page_index": 0,
                "bounds_pt": [10, 10, 100, 100],
                "text": inst.get("text", "Sample Text"),
                "paragraph_style": None
            })

        return {
            "document": {
                "document_id": document_id,
                "expected_revision": expected_revision
            },
            "operations": ops
        }
