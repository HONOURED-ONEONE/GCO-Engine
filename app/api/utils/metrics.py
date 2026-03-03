import time
import numpy as np
from typing import List, Dict, Any

class MetricsTracker:
    def __init__(self):
        self.start_time = time.time()
        self.calls_total = 0
        self.latencies: List[float] = []
        self.custom_metrics: Dict[str, float] = {}

    def record_call(self, duration_ms: float):
        self.calls_total += 1
        self.latencies.append(duration_ms)
        if len(self.latencies) > 1000:
            self.latencies.pop(0)

    def record_custom(self, name: str, value: float):
        if name not in self.custom_metrics:
            self.custom_metrics[name] = 0
        self.custom_metrics[name] += value

    def get_custom(self, name: str, default: float = 0.0) -> float:
        return self.custom_metrics.get(name, default)

    def get_uptime_sec(self) -> int:
        return int(time.time() - self.start_time)

    def get_p50_ms(self) -> int:
        if not self.latencies: return 0
        return int(np.percentile(self.latencies, 50))

    def get_p95_ms(self) -> int:
        if not self.latencies: return 0
        return int(np.percentile(self.latencies, 95))

    def get_summary(self) -> Dict[str, Any]:
        return {
            "uptime_sec": self.get_uptime_sec(),
            "calls_total": self.calls_total,
            "latency_p50_ms": self.get_p50_ms(),
            "latency_p95_ms": self.get_p95_ms(),
            "custom": self.custom_metrics
        }

metrics = MetricsTracker()
