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
            prompt_tokens, completion_tokens, latency_ms, status, session_id=None):

        self._ensure_header()
        scenario_id = session_id if session_id else os.getenv("SCENARIO_ID", "default_scenario")
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
                f"{latency_ms:.2f}",
                status,
                prompt_hash,
                description
            ])

    def get_stats(self, session_id=None):
        """Calculates total usage statistics from the CSV file."""
        if not os.path.exists(self.path):
            return {
                "total_tokens": 0, 
                "total_calls": 0, 
                "avg_latency": 0,
                "input_cost": 0.0,
                "output_cost": 0.0,
                "total_cost": 0.0
            }
        
        total_tokens = 0
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_calls = 0
        total_latency = 0.0
        
        # Prices per million tokens
        input_price_per_m = float(os.getenv("INPUT_PRICE_PER_MILLION", 0))
        output_price_per_m = float(os.getenv("OUTPUT_PRICE_PER_MILLION", 0))
        
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Filter by session_id if provided
                    if session_id and row.get("scenario_id") != session_id:
                        continue

                    try:
                        p_tokens = int(row.get("prompt_tokens", 0))
                        c_tokens = int(row.get("completion_tokens", 0))
                        
                        total_prompt_tokens += p_tokens
                        total_completion_tokens += c_tokens
                        total_tokens += (p_tokens + c_tokens)
                        total_latency += float(row.get("latency_ms", 0))
                        total_calls += 1
                    except ValueError:
                        continue
        except Exception as e:
            print(f"Error reading cost stats: {e}")
            
        input_cost = (total_prompt_tokens / 1_000_000) * input_price_per_m
        output_cost = (total_completion_tokens / 1_000_000) * output_price_per_m
            
        return {
            "total_tokens": total_tokens,
            "total_calls": total_calls,
            "avg_latency": (total_latency / total_calls) if total_calls > 0 else 0,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": input_cost + output_cost
        }