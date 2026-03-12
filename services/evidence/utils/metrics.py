import time

class EvidenceMetrics:
    def __init__(self):
        self.start_time = time.time()
        self.calls_total = 0
        self.latencies = []
        self.audit_failures = 0
        self.downstream_failures = 0
    
    def record_call(self, latency_ms: float):
        self.calls_total += 1
        self.latencies.append(latency_ms)
        # keep last 1000 for memory
        if len(self.latencies) > 1000:
            self.latencies = self.latencies[-1000:]
            
    def record_audit_failure(self):
        self.audit_failures += 1
        
    def record_downstream_failure(self):
        self.downstream_failures += 1
        
    def get_uptime(self) -> float:
        return time.time() - self.start_time
        
    def get_p50(self) -> float:
        if not self.latencies: return 0.0
        return sorted(self.latencies)[int(len(self.latencies) * 0.5)]
        
    def get_p95(self) -> float:
        if not self.latencies: return 0.0
        return sorted(self.latencies)[int(len(self.latencies) * 0.95)]

metrics = EvidenceMetrics()
