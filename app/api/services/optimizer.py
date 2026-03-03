import pandas as pd
import os
import time
import numpy as np
from typing import Dict, Any, Tuple, List
from app.api.services.mode import get_current_mode_data
from app.api.services.corridor import get_active_corridor, corridor_cache
from app.api.utils.io import BASE_DATA_DIR
from app.api.utils.metrics import metrics

# Objective Function Constants
A1, A2 = 0.02, 0.001
T_Q_MIN, F_Q_MIN = 45.0, 5.0
B1, B2 = 0.05, 0.01
T_SWEET = 55.0

# Normalization constants (approximate)
E_MIN, E_MAX = 0.8, 1.7
Y_MIN, Y_MAX = 0.0, 0.8

def calculate_objective(T: float, F: float, weights: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
    # E_hat: Energy proxy (lower is better)
    e_raw = A1 * T + A2 * (F ** 2)
    e_hat = (e_raw - E_MIN) / (E_MAX - E_MIN)
    e_hat = max(0, min(1, e_hat))

    # Q_risk: Quality risk (lower is better)
    q_risk = 0.0
    if T < T_Q_MIN: q_risk += 0.5 * (T_Q_MIN - T)
    if F < F_Q_MIN: q_risk += 0.5 * (F_Q_MIN - F)
    q_risk = min(1.0, q_risk)

    # Y_hat: Yield proxy (higher is better, so we use 1 - Y_hat)
    y_raw = B1 * F - B2 * abs(T - T_SWEET)
    y_hat = (y_raw - Y_MIN) / (Y_MAX - Y_MIN)
    y_hat = max(0, min(1, y_hat))
    
    j_energy = weights.get("energy", 0) * e_hat
    j_quality = weights.get("quality", 0) * q_risk
    j_yield = weights.get("yield", 0) * (1 - y_hat)
    
    total_j = j_energy + j_quality + j_yield
    
    return total_j, {
        "energy": float(j_energy),
        "quality": float(j_quality),
        "yield": float(j_yield),
        "total": float(total_j)
    }

def recommend_setpoints(batch_id: str, ts: str, hints: Dict[str, Any] = None):
    start_time = time.time()
    csv_path = os.path.join(BASE_DATA_DIR, "batches", f"{batch_id}.csv")
    if not os.path.exists(csv_path):
        return None, "Batch not found"

    df = pd.read_csv(csv_path)
    row = df[df['ts'] == ts]
    if row.empty:
        # Try to find closest TS if exact match fails
        try:
            df['ts_dt'] = pd.to_datetime(df['ts'])
            target_dt = pd.to_datetime(ts)
            idx = (df['ts_dt'] - target_dt).abs().idxmin()
            row = df.iloc[[idx]]
        except:
            return None, "Timestamp not found and failed to find closest"

    row_data = row.iloc[0]
    curr_t = float(row_data["temperature"])
    curr_f = float(row_data["flow"])
    
    mode_data = get_current_mode_data()
    weights = mode_data["weights"]
    
    _, corridor = get_active_corridor()
    bounds = corridor["bounds"]
    
    t_bounds = [bounds["temperature"]["lower"], bounds["temperature"]["upper"]]
    f_bounds = [bounds["flow"]["lower"], bounds["flow"]["upper"]]
    
    # Optimizer Params
    max_iters = hints.get("max_iters", 8) if hints else 8
    delta_t = hints.get("delta_temp", 1.0) if hints else 1.0
    delta_f = hints.get("delta_flow", 0.25) if hints else 0.25
    
    # Nudge limits (per step)
    MAX_STEP_T = 2.0
    MAX_STEP_F = 0.5
    
    best_t, best_f = curr_t, curr_f
    best_j, best_breakdown = calculate_objective(best_t, best_f, weights)
    
    # Coordinate Descent
    for _ in range(max_iters):
        improved = False
        # Try T directions
        for nt in [best_t + delta_t, best_t - delta_t]:
            # Clamp to bounds AND nudge limits from ORIGINAL state
            nt = max(t_bounds[0], min(t_bounds[1], nt))
            if abs(nt - curr_t) > MAX_STEP_T:
                nt = curr_t + np.sign(nt - curr_t) * MAX_STEP_T
            
            nj, n_breakdown = calculate_objective(nt, best_f, weights)
            if nj < best_j:
                best_j, best_t, best_breakdown = nj, nt, n_breakdown
                improved = True
                
        # Try F directions
        for nf in [best_f + delta_f, best_f - delta_f]:
            nf = max(f_bounds[0], min(f_bounds[1], nf))
            if abs(nf - curr_f) > MAX_STEP_F:
                nf = curr_f + np.sign(nf - curr_f) * MAX_STEP_F
                
            nj, n_breakdown = calculate_objective(best_t, nf, weights)
            if nj < best_j:
                best_j, best_f, best_breakdown = nj, nf, n_breakdown
                improved = True
        
        if not improved:
            break

    compute_ms = int((time.time() - start_time) * 1000)
    metrics.record_call(compute_ms)
    
    # Rationale
    dom_obj = max(best_breakdown, key=lambda k: best_breakdown[k] if k != 'total' else -1)
    rationale = f"Optimization led by {dom_obj} objective. "
    if best_t > curr_t: rationale += f"Increased temperature to improve {dom_obj}. "
    elif best_t < curr_t: rationale += f"Decreased temperature to improve {dom_obj}. "
    
    if best_f > curr_f: rationale += f"Increased flow to improve {dom_obj}. "
    elif best_f < curr_f: rationale += f"Decreased flow to improve {dom_obj}. "
    
    if best_t == t_bounds[0] or best_t == t_bounds[1]: rationale += "Temperature hit corridor bound. "
    if best_f == f_bounds[0] or best_f == f_bounds[1]: rationale += "Flow hit corridor bound. "
    
    if abs(best_t - curr_t) >= MAX_STEP_T: rationale += "T-nudge limited by safety jump. "
    if abs(best_f - curr_f) >= MAX_STEP_F: rationale += "F-nudge limited by safety jump. "

    return {
        "setpoints": {"temperature": round(best_t, 2), "flow": round(best_f, 2)},
        "within_bounds": True,
        "objective_weights": weights,
        "objective_breakdown": best_breakdown,
        "constraints": {"temperature": t_bounds, "flow": f_bounds},
        "nudge_applied": {"temperature": round(best_t - curr_t, 2), "flow": round(best_f - curr_f, 2)},
        "compute_ms": compute_ms,
        "rationale": rationale.strip()
    }, None

def get_preview(batch_id: str, window: int, step_sec: int):
    start_time = time.time()
    csv_path = os.path.join(BASE_DATA_DIR, "batches", f"{batch_id}.csv")
    if not os.path.exists(csv_path):
        return None, "Batch not found"
    
    df = pd.read_csv(csv_path)
    # Start from some point, let's say middle or beginning
    # For preview, we'll just take 'window' rows from the start or a sample
    points = []
    mode_data = get_current_mode_data()
    weights = mode_data["weights"]
    
    # Limit window to available data
    actual_window = min(window, len(df))
    subset = df.head(actual_window)
    
    _, corridor = get_active_corridor()
    bounds = corridor["bounds"]
    t_bounds = [bounds["temperature"]["lower"], bounds["temperature"]["upper"]]
    f_bounds = [bounds["flow"]["lower"], bounds["flow"]["upper"]]
    
    for _, row in subset.iterrows():
        ts = row['ts']
        curr_t = float(row['temperature'])
        curr_f = float(row['flow'])
        
        # Call recommend logic internally without re-reading files
        # We'll just do a single-step optimization for each point in preview
        rec, _ = recommend_setpoints(batch_id, ts)
        
        points.append({
            "ts": ts,
            "state": {"temperature": curr_t, "flow": curr_f},
            "setpoints": rec["setpoints"],
            "objective_total": rec["objective_breakdown"]["total"],
            "bounds": {
                "temperature": t_bounds,
                "flow": f_bounds
            }
        })
        
    compute_ms = int((time.time() - start_time) * 1000)
    return {
        "horizon": window,
        "step_sec": step_sec,
        "points": points,
        "compute_ms": compute_ms,
        "note": "Deterministic synthetic preview; no PLC write-back."
    }, None
