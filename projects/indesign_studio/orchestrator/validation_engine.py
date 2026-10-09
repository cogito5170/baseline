import json
import os
import jsonschema

class ValidationEngine:
    def __init__(self, schemas_dir="../contracts"):
        self.schemas_dir = schemas_dir
        self.schemas = {}
        # We only really need indesign_edit_spec for now
        schema_path = f"{schemas_dir}/indesign_edit_spec_v1.json"
        if os.path.exists(schema_path):
            with open(schema_path) as f:
                self.schemas["indesign_edit_spec"] = json.load(f)

    def validate_spec(self, spec):
        if "indesign_edit_spec" in self.schemas:
            try:
                jsonschema.validate(instance=spec, schema=self.schemas["indesign_edit_spec"])
            except jsonschema.exceptions.ValidationError as e:
                return False, str(e)
        
        # Check that operations don't go off-page or have inverted bounds.
        # This is a basic structural validation.
        for op in spec.get("operations", []):
            if op["op"] == "create_text_frame":
                bounds = op.get("bounds_pt", [])
                if len(bounds) == 4:
                    top, left, bottom, right = bounds
                    if top >= bottom or left >= right:
                        return False, "Inverted bounds"
        return True, ""
