import csv
import os
import time
import hashlib
from datetime import datetime
from uuid import uuid4

class CostLogger:
    def __init__(self, path="costs.csv"):
        self.path = path
        self.initialized = False

    def _ensure_header(self):
        if not self.initialized and not os.path.exists(self.path):
            with open(self.path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp",
                    "scenario_id",
                    "call_id",
                    "model",
                    "endpoint",
                    "prompt_tokens",
                    "completion_tokens",
                    "total_tokens",
                    "latency_ms",
                    "status",
                    "prompt_hash",
                    "notes"
                ])
        self.initialized = True

    def log(self, *, model, endpoint, prompt,
            prompt_tokens, completion_tokens, latency_ms, status):

        self._ensure_header()
        scenario_id = os.getenv("SCENARIO_ID", "default_scenario")
        description = os.getenv("SCENARIO_DESCRIPTION", "No description")
        call_id = str(uuid4())
        prompt_hash = hashlib.sha256(prompt.encode('utf-8')).hexdigest()

        with open(self.path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                scenario_id,
                call_id,
                model,
                endpoint,
                prompt_tokens,
                completion_tokens,
                prompt_tokens + completion_tokens,
                latency_ms,
                status,
                prompt_hash,
                description
            ])