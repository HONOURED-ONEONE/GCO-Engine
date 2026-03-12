import pandas as pd
import os
import time
import numpy as np
from typing import Dict, Any, Tuple, Optional
import casadi as ca

from services.optimizer.utils.metrics import metrics

BASE_DATA_DIR = os.path.join(os.getcwd(), "data")

# NMPC Parameters
Hp = 10  # Prediction horizon
Hu = 3   # Control horizon
Ts = 10  # Sampling time (seconds)

# Process Model Constants
TAU_T = 60.0  # Temperature time constant (s)
TAU_F = 15.0  # Flow time constant (s)
K_T = 0.5     # Temp gain
K_F = 1.0     # Flow gain

class NMPCController:
    def __init__(self):
        self.nx = 2  # States: [T, F]
        self.nu = 2  # Inputs: [T_sp, F_sp]
        self.solver = None
        self._last_u = np.array([55.0, 10.0])
        self._setup_solver()

    def _setup_solver(self):
        # States
        x = ca.SX.sym('x', self.nx)
        # Inputs
        u = ca.SX.sym('u', self.nu)
        
        # Continuous time dynamics: dx/dt = f(x, u)
        x_dot = ca.vertcat(
            (K_T * u[0] * 2.0 - x[0]) / TAU_T, 
            (K_F * u[1] - x[1]) / TAU_F
        )
        
        # Discretization (RK4)
        f = ca.Function('f', [x, u], [x_dot])
        X0 = ca.SX.sym('X0', self.nx)
        U = ca.SX.sym('U', self.nu)
        
        dt = Ts
        k1 = f(X0, U)
        k2 = f(X0 + dt/2 * k1, U)
        k3 = f(X0 + dt/2 * k2, U)
        k4 = f(X0 + dt * k3, U)
        X_next = X0 + dt/6 * (k1 + 2*k2 + 2*k3 + k4)
        F_disc = ca.Function('F_disc', [X0, U], [X_next])

        # Optimization variables
        OPT_X = ca.SX.sym('OPT_X', self.nx, Hp + 1)
        OPT_U = ca.SX.sym('OPT_U', self.nu, Hp)
        P = ca.SX.sym('P', self.nx + 3) # Initial state + weights [energy, quality, yield]

        obj = 0
        g = []
        
        # Initial condition constraint
        g.append(OPT_X[:, 0] - P[:self.nx])
        
        # Weights
        w_energy = P[self.nx]
        w_quality = P[self.nx+1]
        w_yield = P[self.nx+2]

        for k in range(Hp):
            # Dynamic constraints
            g.append(OPT_X[:, k+1] - F_disc(OPT_X[:, k], OPT_U[:, k]))
            
            T, F = OPT_X[0, k], OPT_X[1, k]
            
            # Energy proxy
            e_hat = (0.02 * T + 0.001 * (F**2) - 0.8) / 0.9
            
            # Quality risk (soft constraint penalty)
            q_risk = ca.fmax(0, 45 - T) + ca.fmax(0, 5 - F)
            
            # Yield proxy
            y_hat = (0.05 * F - 0.01 * ca.fabs(T - 55.0)) / 0.8
            
            obj += w_energy * e_hat + w_quality * q_risk + w_yield * (1 - y_hat)
            
            # Rate of change penalty
            if k > 0:
                obj += 0.1 * ca.sumsqr(OPT_U[:, k] - OPT_U[:, k-1])

        # Flatten variables
        vars = ca.vertcat(ca.reshape(OPT_X, -1, 1), ca.reshape(OPT_U, -1, 1))
        
        opts = {
            'ipopt.print_level': 0,
            'print_time': 0,
            'ipopt.max_iter': 50,
            'ipopt.tol': 1e-3
        }
        
        nlp = {'x': vars, 'f': obj, 'g': ca.vertcat(*g), 'p': P}
        self.solver = ca.nlpsol('solver', 'ipopt', nlp, opts)
        self.vars_size = vars.size1()
        self.g_size = ca.vertcat(*g).size1()

    def solve(self, x0: np.ndarray, weights: Dict[str, float], bounds: Dict[str, Any]) -> Tuple[Optional[np.ndarray], str]:
        p = np.array([x0[0], x0[1], weights.get('energy', 0), weights.get('quality', 0), weights.get('yield', 0)])
        
        # Bounds
        lbg = np.zeros(self.g_size)
        ubg = np.zeros(self.g_size)
        
        lbx = -np.inf * np.ones(self.vars_size)
        ubx = np.inf * np.ones(self.vars_size)
        
        # State bounds (OPT_X)
        for k in range(Hp + 1):
            lbx[k*2] = bounds['temperature']['lower']
            ubx[k*2] = bounds['temperature']['upper']
            lbx[k*2+1] = bounds['flow']['lower']
            ubx[k*2+1] = bounds['flow']['upper']
            
        # Input bounds (OPT_U)
        u_start = (Hp + 1) * 2
        for k in range(Hp):
            lbx[u_start + k*2] = bounds['temperature']['lower']
            ubx[u_start + k*2] = bounds['temperature']['upper']
            lbx[u_start + k*2+1] = bounds['flow']['lower']
            ubx[u_start + k*2+1] = bounds['flow']['upper']

        try:
            sol = self.solver(lbx=lbx, ubx=ubx, lbg=lbg, ubg=ubg, p=p)
            u_opt = sol['x'][(Hp+1)*2:(Hp+1)*2+2].full().flatten()
            status = self.solver.stats()['return_status']
            return u_opt, status
        except Exception as e:
            return None, str(e)

_nmpc = NMPCController()

def heuristic_nudge(curr_t: float, curr_f: float, weights: Dict[str, float], bounds: Dict[str, Any]) -> Dict[str, float]:
    """Deterministic fallback: slight nudge towards 'sweet spot' within bounds."""
    t_target = 55.0
    f_target = 10.0
    
    t_step = 0.5 if curr_t < t_target else -0.5
    f_step = 0.1 if curr_f < f_target else -0.1
    
    new_t = max(bounds["temperature"]["lower"], min(bounds["temperature"]["upper"], curr_t + t_step))
    new_f = max(bounds["flow"]["lower"], min(bounds["flow"]["upper"], curr_f + f_step))
    
    return {"temperature": round(new_t, 2), "flow": round(new_f, 2)}

def recommend_setpoints(batch_id: str, ts: str = None, hints: Dict[str, Any] = None, live_state: Optional[Dict[str, float]] = None, bounds: Dict[str, Any] = None, weights: Dict[str, float] = None) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    start_time = time.time()
    
    if bounds is None: bounds = {}
    if weights is None: weights = {}
    
    if live_state:
        curr_t = float(live_state["temperature"])
        curr_f = float(live_state["flow"])
    else:
        csv_path = os.path.join(BASE_DATA_DIR, "batches", f"{batch_id}.csv")
        if not os.path.exists(csv_path):
            return None, "Batch not found"

        df = pd.read_csv(csv_path)
        if ts is None:
             row = df.iloc[[-1]]
        else:
             row = df[df['ts'] == ts]
             
        if row.empty:
            try:
                df['ts_dt'] = pd.to_datetime(df['ts'])
                target_dt = pd.to_datetime(ts)
                idx = (df['ts_dt'] - target_dt).abs().idxmin()
                row = df.iloc[[idx]]
            except:
                return None, "Timestamp not found"

        row_data = row.iloc[0]
        curr_t = float(row_data["temperature"])
        curr_f = float(row_data["flow"])
    
    # Optional Future hooks
    if hints:
        if hints.get("restraint"):
            pass # Hook point for shorter horizon or stricter changes

    # NMPC Solve
    x0 = np.array([curr_t, curr_f])
    u_opt, status = _nmpc.solve(x0, weights, bounds)
    
    fallback_active = False
    if u_opt is None or status != 'Solve_Succeeded':
        u_opt_dict = heuristic_nudge(curr_t, curr_f, weights, bounds)
        u_opt = np.array([u_opt_dict["temperature"], u_opt_dict["flow"]])
        fallback_active = True
        metrics.record_custom("solver_timeouts", 1)
    else:
        metrics.record_custom("solver_success", 1)

    compute_ms = int((time.time() - start_time) * 1000)
    metrics.record_call(compute_ms)

    return {
        "setpoints": {"temperature": round(float(u_opt[0]), 2), "flow": round(float(u_opt[1]), 2)},
        "within_bounds": True,
        "objective_weights": weights,
        "constraints": bounds,
        "compute_ms": compute_ms,
        "fallback_active": fallback_active,
        "solver_status": status,
        "rationale": "NMPC optimized trajectory." if not fallback_active else "Heuristic fallback nudge due to solver failure."
    }, None

def get_preview(batch_id: str, window: int, step_sec: int, bounds: Dict[str, Any] = None, weights: Dict[str, float] = None) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    start_time = time.time()
    
    if bounds is None: bounds = {}
    if weights is None: weights = {}
    
    csv_path = os.path.join(BASE_DATA_DIR, "batches", f"{batch_id}.csv")
    if not os.path.exists(csv_path):
        return None, "Batch not found"
    
    df = pd.read_csv(csv_path)
    actual_window = min(window, len(df))
    subset = df.head(actual_window)
    
    points = []
    for _, row in subset.iterrows():
        ts = row['ts']
        rec, _ = recommend_setpoints(batch_id, ts, bounds=bounds, weights=weights)
        points.append({
            "ts": ts,
            "state": {"temperature": float(row['temperature']), "flow": float(row['flow'])},
            "setpoints": rec["setpoints"],
            "bounds": bounds,
            "fallback": rec["fallback_active"]
        })
        
    return {
        "horizon": window,
        "step_sec": step_sec,
        "points": points,
        "compute_ms": int((time.time() - start_time) * 1000)
    }, None
