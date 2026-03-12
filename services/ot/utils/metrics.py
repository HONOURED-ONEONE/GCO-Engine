import time
from typing import Dict, List, Any
import statistics

class Metrics:
    def __init__(self):
        self.start_time = time.time()
        self.calls_total = 0
        self.opcua_connect_failures = 0
        self.write_failures = 0
        self.reverts = 0
        self.audit_failures = 0
        self.latencies: List[float] = []

    def record_call(self, latency_ms: float):
        self.calls_total += 1
        self.latencies.append(latency_ms)
        if len(self.latencies) > 1000:
            self.latencies = self.latencies[-1000:]

    def get_health(self) -> Dict[str, Any]:
        uptime = time.time() - self.start_time
        p50 = statistics.median(self.latencies) if self.latencies else 0.0
        p95 = statistics.quantiles(self.latencies, n=20)[18] if len(self.latencies) >= 20 else p50
        
        return {
            "uptime_sec": uptime,
            "calls_total": self.calls_total,
            "p50_latency_ms": p50,
            "p95_latency_ms": p95,
            "opcua_connect_failures": self.opcua_connect_failures,
            "write_failures": self.write_failures,
            "reverts": self.reverts,
            "audit_failures": self.audit_failures
        }

metrics = Metrics()
