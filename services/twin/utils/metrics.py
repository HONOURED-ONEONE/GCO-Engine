import time
from typing import Dict, Any

class TwinMetrics:
    def __init__(self):
        self.runs_started = 0
        self.counterfactuals_run = 0
        self.pilots_started = 0
        self.total_sim_steps = 0
        self.errors = 0

    def get_summary(self) -> Dict[str, Any]:
        return {
            "runs_started": self.runs_started,
            "counterfactuals_run": self.counterfactuals_run,
            "pilots_started": self.pilots_started,
            "total_sim_steps": self.total_sim_steps,
            "errors": self.errors,
            "ts": time.time()
        }

metrics_tracker = TwinMetrics()
