from typing import List
import time

class MetricsStore:
    def __init__(self):
        self.calls_total = 0
        self.provider_failures = 0
        self.audit_post_failures = 0
        self.latencies: List[float] = []

    def record_call(self):
        self.calls_total += 1

    def record_provider_failure(self):
        self.provider_failures += 1

    def record_audit_failure(self):
        self.audit_post_failures += 1

    def record_latency(self, latency_ms: float):
        self.latencies.append(latency_ms)
        # Keep only the last 1000 to avoid unbounded growth
        if len(self.latencies) > 1000:
            self.latencies.pop(0)

    def get_p95_ms(self) -> float:
        if not self.latencies:
            return 0.0
        sorted_lat = sorted(self.latencies)
        idx = int(len(sorted_lat) * 0.95)
        return sorted_lat[idx]

metrics = MetricsStore()
