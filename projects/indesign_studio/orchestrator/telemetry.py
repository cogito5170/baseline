import json
import os
import time

class Telemetry:
    def __init__(self, log_file="telemetry.jsonl"):
        self.log_file = log_file

    def log(self, event_type, data):
        record = {
            "timestamp": time.time(),
            "event_type": event_type,
            "data": data
        }
        with open(self.log_file, "a") as f:
            f.write(json.dumps(record) + "\n")
