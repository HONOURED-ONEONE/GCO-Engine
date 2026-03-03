import requests
import time
import numpy as np
import sys

lats = []
for _ in range(200):
    try:
        start = time.time()
        r = requests.post('http://localhost:8000/optimize/recommend', 
                          json={'batch_id': 'batch_001', 'ts': '2026-03-03T10:00:00Z'},
                          timeout=5)
        lats.append((time.time() - start) * 1000)
    except Exception as e:
        pass

if lats:
    print(f"p50: {np.percentile(lats, 50):.2f} ms | p95: {np.percentile(lats, 95):.2f} ms")
else:
    print("No data collected. Is the API running?")
