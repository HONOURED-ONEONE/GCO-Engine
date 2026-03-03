import time
import numpy as np
from typing import List

class MetricsTracker:
    def __init__(self):
        self.start_time = time.time()
        self.calls_total = 0
        self.latencies: List[float] = []

    def record_call(self, duration_ms: float):
        self.calls_total += 1
        self.latencies.append(duration_ms)
        if len(self.latencies) > 1000:
            self.latencies.pop(0)

    def get_uptime_sec(self) -> int:
        return int(time.time() - self.start_time)

    def get_p50_ms(self) -> int:
        if not self.latencies: return 0
        return int(np.percentile(self.latencies, 50))

    def get_p95_ms(self) -> int:
        if not self.latencies: return 0
        return int(np.percentile(self.latencies, 95))

metrics = MetricsTracker()
