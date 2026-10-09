import copy
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from magorch import contracts

class ArtifactStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._meta_dir = self.root.parent / ".magorch_meta"
        self._meta_dir.mkdir(parents=True, exist_ok=True)

    def _meta_path(self, artifact_id):
        return self._meta_dir / f"{artifact_id}.json"

    def _read_meta(self, artifact_id):
        path = self._meta_path(artifact_id)
        if not path.exists():
            return {"versions": []}
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_meta(self, artifact_id, meta):
        self._meta_path(artifact_id).write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")

    def latest_version(self, artifact_id):
        meta = self._read_meta(artifact_id)
        if not meta["versions"]:
            return None
        return len(meta["versions"])

    def put(self, artifact_id, artifact_type, payload, *, produced_by, inputs=(), media_type="application/json", approval_required=True):
        if isinstance(payload, dict):
            if "schema" in payload:
                contracts.validate(payload)
            if "artifact_id" in payload and payload["artifact_id"] != artifact_id:
                raise ValueError("artifact_id mismatch")
            
        meta = self._read_meta(artifact_id)
        version = len(meta["versions"]) + 1
        
        if isinstance(payload, dict):
            if "version" in payload and payload["version"] != version:
                raise ValueError(f"version mismatch, expected {version} got {payload['version']}")

        file_ext = ".json" if media_type == "application/json" else ".bin"
        if media_type == "application/pdf":
            file_ext = ".pdf"
        file_path = self.root / f"{artifact_id}_v{version}{file_ext}"
        
        if isinstance(payload, bytes):
            if media_type == "application/json":
                raise TypeError("bytes payload requires non-json media_type")
            if media_type is None:
                raise ValueError("bytes payload requires media_type")
            file_path.write_bytes(payload)
            sha256 = hashlib.sha256(payload).hexdigest()
        else:
            data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            file_path.write_bytes(data_bytes)
            sha256 = hashlib.sha256(data_bytes).hexdigest()
        
        # record
        rec = {
            "artifact_id": artifact_id,
            "version": version,
            "artifact_type": artifact_type,
            "schema": payload.get("schema") if isinstance(payload, dict) else None,
            "media_type": media_type,
            "sha256": sha256,
            "path": f"artifacts/{file_path.name}",
            "produced_by": produced_by,
            "inputs": list(inputs),
            "validation_status": "passed" if isinstance(payload, dict) and "schema" in payload else "not_applicable",
            "approval_status": "pending" if approval_required else "not_required",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        meta["versions"].append(rec)
        self._write_meta(artifact_id, meta)
        
        return {"artifact_id": artifact_id, "version": version}

    def get(self, artifact_id, version=None):
        meta = self._read_meta(artifact_id)
        if not meta["versions"]:
            raise KeyError(artifact_id)
        
        if version is None:
            rec = meta["versions"][-1]
        else:
            if version < 1 or version > len(meta["versions"]):
                raise KeyError(f"{artifact_id} v{version}")
            rec = meta["versions"][version - 1]
            
        file_path = self.root.parent / rec["path"]
        if not file_path.exists():
            raise KeyError(artifact_id)
            
        if rec["media_type"] == "application/json":
            return json.loads(file_path.read_text(encoding="utf-8"))
        else:
            return file_path.read_bytes()

    def record(self, artifact_id, version):
        meta = self._read_meta(artifact_id)
        if not meta["versions"] or version < 1 or version > len(meta["versions"]):
            raise KeyError(f"{artifact_id} v{version}")
        return copy.deepcopy(meta["versions"][version - 1])

    def approve(self, artifact_id, version, by):
        meta = self._read_meta(artifact_id)
        meta["versions"][version - 1]["approval_status"] = "approved"
        # we could record `by` but not strictly required by the basic schema
        self._write_meta(artifact_id, meta)

    def reject(self, artifact_id, version, by, note=""):
        meta = self._read_meta(artifact_id)
        meta["versions"][version - 1]["approval_status"] = "rejected"
        self._write_meta(artifact_id, meta)

    def approval_status(self, artifact_id, version):
        meta = self._read_meta(artifact_id)
        if version < 1 or version > len(meta["versions"]):
            raise KeyError()
        return meta["versions"][version - 1]["approval_status"]

    def manifest(self, project_id):
        artifacts = []
        for path in self._meta_dir.glob("*.json"):
            meta = json.loads(path.read_text(encoding="utf-8"))
            artifacts.extend(meta["versions"])
        return {
            "schema": "artifact_manifest/1",
            "project_id": project_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "artifacts": artifacts
        }
