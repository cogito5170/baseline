import json
from pathlib import Path
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

class ContractError(ValueError):
    def __init__(self, message, errors=None):
        super().__init__(message)
        self.errors = errors if errors else [message]

_registry = Registry()
_schemas = {}

def _load_core():
    global _registry
    root = Path(__file__).resolve().parents[1] / "contracts"
    for path in root.glob("*.schema.json"):
        with open(path, "r", encoding="utf-8") as f:
            schema = json.load(f)
            name = schema["$id"].split("urn:magorch:")[1].split(":")[0]
            major = schema["$id"].split("urn:magorch:")[1].split(":")[1]
            key = f"{name}/{major}"
            resource = Resource.from_contents(schema)
            _registry = _registry.with_resource(schema["$id"], resource)
            _schemas[key] = schema

def register(name, schema):
    global _registry
    if name in _schemas:
        if _schemas[name] != schema:
            raise ContractError(f"Contract {name} already registered with different schema", [])
        return
    _schemas[name] = schema
    if "$id" in schema:
        _registry = _registry.with_resource(schema["$id"], Resource.from_contents(schema))

def names():
    return list(_schemas.keys())

def validate(doc, schema=None):
    if not isinstance(doc, dict):
        raise ContractError("Document must be a dictionary", [])
    
    if schema is None:
        if "schema" not in doc:
            raise ContractError("Missing schema field", [])
        schema = doc["schema"]
    
    if schema not in _schemas:
        raise ContractError(f"Unknown schema {schema}", [])
    
    # We should validate against the actual schema in registry if possible
    validator = Draft202012Validator(_schemas[schema], registry=_registry)
    errors = []
    for error in validator.iter_errors(doc):
        # build JSONPath-like string
        path = "$"
        for p in error.path:
            path += f".{p}"
        errors.append(f"{path}: {error.message}")
    
    if errors:
        raise ContractError("Validation failed", errors)

_load_core()
