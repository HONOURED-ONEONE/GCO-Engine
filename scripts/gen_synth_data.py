import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

def generate_batch(batch_id: str, start_time: datetime, rows: int = 120):
    data = []
    
    # Baseline process variables
    temp = 150.0
    flow = 12.0
    
    for i in range(rows):
        ts = (start_time + timedelta(minutes=i)).isoformat() + "Z"
        
        # Add random walk drift
        temp += np.random.normal(0, 0.2)
        flow += np.random.normal(0, 0.05)
        
        energy_kwh_inst = 0.5 * (temp / 10.0) + 2.0 * flow + np.random.normal(0, 0.1)
        yield_proxy = 0.95 + np.random.normal(0, 0.01)
        quality_signal = 1 if (146 < temp < 154 and 10.5 < flow < 13.5) else 0
        
        data.append({
            "ts": ts,
            "temperature": round(temp, 2),
            "flow": round(flow, 2),
            "energy_kwh_inst": round(energy_kwh_inst, 2),
            "quality_signal": quality_signal,
            "yield_proxy": round(yield_proxy, 4)
        })
        
    df = pd.DataFrame(data)
    save_path = os.path.join("data", "batches", f"{batch_id}.csv")
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    df.to_csv(save_path, index=False)
    print(f"Generated {save_path}")

if __name__ == "__main__":
    now = datetime(2026, 3, 3, 10, 0, 0)
    generate_batch("batch_001", now)
    generate_batch("batch_002", now + timedelta(hours=4))
    generate_batch("batch_003", now + timedelta(hours=8))
