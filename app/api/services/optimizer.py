import pandas as pd
import os
from typing import Dict, Any
from app.api.services.mode import get_current_weights
from app.api.services.corridor import get_active_corridor
from app.api.utils.io import BASE_DATA_DIR

def recommend_setpoints(batch_id: str, ts: str):
    csv_path = os.path.join(BASE_DATA_DIR, "batches", f"{batch_id}.csv")
    if not os.path.exists(csv_path):
        return None, "Batch not found", False, {}

    df = pd.read_csv(csv_path)
    # Match TS string or find closest
    row = df[df['ts'] == ts]
    if row.empty:
        return None, "Timestamp not found in batch", False, {}

    row = row.iloc[0]
    weights = get_current_weights()
    _, corridor = get_active_corridor()
    bounds = corridor["bounds"]
    
    setpoints = {}
    rationale_parts = []
    within_bounds = True

    for param in ["temperature", "flow"]:
        if param not in bounds:
            continue
            
        val = float(row[param])
        lower = bounds[param]["lower"]
        upper = bounds[param]["upper"]
        center = (lower + upper) / 2.0
        
        if val < lower:
            rec = lower + 0.1 * (center - lower)
            rationale_parts.append(f"{param} ({val}) is below lower bound ({lower}). Increasing toward center.")
            within_bounds = False
        elif val > upper:
            rec = upper - 0.1 * (upper - center)
            rationale_parts.append(f"{param} ({val}) is above upper bound ({upper}). Decreasing toward center.")
            within_bounds = False
        else:
            # Within bounds, nudge based on mode
            if weights.get("energy", 0) > 0.5: # sustainability
                # Assume lower temperature or flow saves energy
                rec = val - 0.05 * (val - lower)
                rationale_parts.append(f"Sustainability mode: Nudging {param} down to reduce energy while staying in bounds.")
            else:
                # Production mode: move toward center for stability
                rec = val + 0.1 * (center - val)
                rationale_parts.append(f"Production mode: Centering {param} for process stability.")
        
        setpoints[param] = round(rec, 1)

    rationale = " | ".join(rationale_parts)
    return setpoints, rationale, within_bounds, weights
