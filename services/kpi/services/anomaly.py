import os
import numpy as np

def compute_rolling_percentiles(items, field, n=10):
    if not items:
        return 0.0, 0.0
    
    recent_items = items[-n:]
    values = [item[field] for item in recent_items if field in item]
    
    if not values:
        return 0.0, 0.0
        
    p10 = np.percentile(values, 10)
    p90 = np.percentile(values, 90)
    
    return float(p10), float(p90)

def is_anomalous(item, rolling_p10_p90, thresholds):
    reasons = []
    
    # Rule A
    if item.get("quality_deviation", False):
        reasons.append("quality_deviation")
        
    # Rule B
    yield_min = float(os.getenv("YIELD_MIN", "80.0"))
    if item.get("yield_pct", 100.0) < yield_min:
        reasons.append("low_yield")
        
    # Rule C
    if rolling_p10_p90 and "energy_kwh" in item:
        p10, p90 = rolling_p10_p90
        energy = item["energy_kwh"]
        # Only check bounds if we have meaningful non-zero percentiles or enough history
        # but the spec says "energy_kwh outside [p10, p90] of last N=10 batches".
        # We need to make sure we don't flag the very first batch just because p10=p90=energy
        # Actually if energy < p10 or energy > p90. For the first batch p10=p90=energy, so it's not outside.
        if p10 < p90: # Only if there is a spread
            if energy < p10 or energy > p90:
                reasons.append("energy_out_of_band")
        elif energy != p10 and len(thresholds.get("items", [])) > 0:
            # if p10 == p90 but energy is different, it is out of band
            reasons.append("energy_out_of_band")

    is_anomaly = len(reasons) > 0
    return is_anomaly, reasons
