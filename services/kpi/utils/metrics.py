import time
from contextlib import contextmanager
import numpy as np

# In-memory metrics
class KPIMetrics:
    def __init__(self):
        self.start_time = time.time()
        self.calls_total = 0
        self.anomalies_total = 0
        self.upserts_total = 0
        self.governance_audit_failures = 0
        self.policy_notify_failures = 0
        self.latencies = []

    def record_latency(self, latency_ms: float):
        self.latencies.append(latency_ms)
        # Keep last 1000 for memory safety
        if len(self.latencies) > 1000:
            self.latencies = self.latencies[-1000:]
            
    def get_uptime(self) -> float:
        return time.time() - self.start_time
        
    def get_p50_p95(self):
        if not self.latencies:
            return 0.0, 0.0
        return float(np.percentile(self.latencies, 50)), float(np.percentile(self.latencies, 95))

metrics = KPIMetrics()

@contextmanager
def timer():
    start = time.perf_counter()
    yield
    end = time.perf_counter()
    latency_ms = (end - start) * 1000
    metrics.record_latency(latency_ms)
