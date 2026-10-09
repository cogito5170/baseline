"""Shared helpers for the acceptance tests (spec side; the implementer must not edit tests/)."""
import copy
import json
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CONTRACTS = ROOT / "contracts"
EXAMPLES = CONTRACTS / "examples"

NOTE_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "urn:magorch:test_note:1",
    "type": "object",
    "required": ["schema", "text"],
    "additionalProperties": False,
    "properties": {
        "schema": {"const": "test_note/1"},
        "artifact_id": {"type": "string"},
        "version": {"type": "integer", "minimum": 1},
        "text": {"type": "string", "minLength": 1},
    },
}


def register_note():
    from magorch import contracts
    if "test_note/1" not in contracts.names():
        contracts.register("test_note/1", NOTE_SCHEMA)


def example(name):
    return json.loads((EXAMPLES / f"{name}.json").read_text(encoding="utf-8"))


def task(task_id, role, *, deps=(), inputs=(), out_ids=None, max_attempts=2, timeout=5.0, revision_limit=2,
         on_change="rerun", objective=None):
    """An agent_task/1 producing test_note/1 artifacts. inputs: artifact ids bound to latest (version null)."""
    t = {
        "schema": "agent_task/1",
        "task_id": task_id,
        "project_id": "MAG-2026-901",
        "agent_role": role,
        "objective": objective or f"produce notes for {task_id}",
        "inputs": [{"artifact_id": a, "version": None} for a in inputs],
        "instructions": {"required_actions": ["write the note"], "forbidden_actions": ["invent sources"]},
        "output_contract": {"schema": "test_note/1", "artifact_type": "note"},
        "dependencies": list(deps),
        "acceptance_criteria": ["note text is not empty"],
        "constraints": {"max_attempts": max_attempts, "timeout_seconds": timeout, "revision_limit": revision_limit,
                        "on_upstream_change": on_change},
        "status": "pending",
    }
    if out_ids is not None:
        t["output_contract"]["artifact_ids"] = list(out_ids)
    return t


class Recorder:
    """Agent factory that records calls (task copy, inputs copy, start/end times) per task id."""

    def __init__(self):
        self.calls = []
        self.lock = threading.Lock()
        self.active = 0
        self.max_active = 0

    def agent(self, out_for=None, sleep=0.0, text=None, fail_times=0, bad_times=0, mutate_inputs=False):
        """out_for: task_id -> list of artifact ids to produce (default ART-<TASKSUFFIX>)."""
        counters = {}

        def run(task, inputs):
            tid = task["task_id"]
            with self.lock:
                self.active += 1
                self.max_active = max(self.max_active, self.active)
                n = counters[tid] = counters.get(tid, 0) + 1
                self.calls.append({"task_id": tid, "task": copy.deepcopy(task), "inputs": copy.deepcopy(inputs),
                                   "start": time.monotonic(), "n": n})
                rec = self.calls[-1]
            try:
                if sleep:
                    time.sleep(sleep)
                if mutate_inputs:
                    for v in inputs.values():
                        if isinstance(v, dict):
                            v["text"] = "MUTATED BY AGENT"
                if n <= fail_times:
                    raise RuntimeError(f"simulated failure {n}")
                ids = (out_for or {}).get(tid) or ["ART-" + tid.removeprefix("TASK-")]
                bad = n <= fail_times + bad_times
                arts = []
                for aid in ids:
                    payload = {"schema": "test_note/1", "text": text or f"{tid} from {sorted(inputs)} v{n}"}
                    if bad:
                        payload = {"schema": "test_note/1", "text": ""}  # violates minLength
                    arts.append({"artifact_id": aid, "artifact_type": "note", "payload": payload})
                return {"artifacts": arts, "issues": [], "unresolved_questions": [],
                        "provenance": {"model_provider": None, "model_id": None}}
            finally:
                with self.lock:
                    self.active -= 1
                    rec["end"] = time.monotonic()

        return run

    def calls_for(self, task_id):
        return [c for c in self.calls if c["task_id"] == task_id]
