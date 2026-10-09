import json
import os

class JobState:
    def __init__(self, state_file="job_state.json"):
        self.state_file = state_file
        self.state = {
            "status": "requested",
            "applied_ops": [],
            "revision_rounds": 0,
            "document_revision": 0
        }
        self.load()

    def load(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, "r") as f:
                self.state = json.load(f)

    def save(self):
        with open(self.state_file, "w") as f:
            json.dump(self.state, f)

    def record_op(self, op_id):
        if op_id not in self.state["applied_ops"]:
            self.state["applied_ops"].append(op_id)
            self.save()
            return True
        return False # Already applied

    def is_op_applied(self, op_id):
        return op_id in self.state["applied_ops"]

    def increment_revision(self):
        self.state["revision_rounds"] += 1
        self.save()
        if self.state["revision_rounds"] > 3:
            raise Exception("Max revision rounds exceeded")

    def set_status(self, status):
        self.state["status"] = status
        self.save()
