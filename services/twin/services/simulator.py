import random
import math
from typing import Dict, Any, List, Tuple, Optional
from ..models.schemas import ScenarioConfig

class Simulator:
    @staticmethod
    def simulate_step(
        state: Dict[str, float],
        setpoints: Dict[str, float],
        scenario: ScenarioConfig,
        step_index: int,
        seed: int
    ) -> Dict[str, float]:
        """
        Deterministic simulation step.
        """
        # Set seed for repeatability within the step
        # Combine base seed with step_index to ensure each step is unique but deterministic
        step_seed = seed + step_index
        rng = random.Random(step_seed)

        new_state = state.copy()
        
        # Simplified process model: Thermal + Flow
        # temperature = f(temp_prev, heat_input, ambient_dist)
        params = scenario.parameters
        
        # Base physics: temperature converges to setpoint with some inertia
        heat_input = setpoints.get("temperature", state.get("temperature", 25.0))
        inertia = params.get("thermal_inertia", 0.8)
        
        # Apply disturbances from scenario
        disturbance_cfg = scenario.disturbance_model
        noise_level = disturbance_cfg.get("noise", 0.0)
        noise = rng.uniform(-noise_level, noise_level)
        
        drift_level = disturbance_cfg.get("drift", 0.0)
        drift = drift_level * step_index
        
        # Update temperature
        new_state["temperature"] = (state.get("temperature", 25.0) * inertia + 
                                   heat_input * (1 - inertia) + 
                                   noise + drift)
        
        # Update pressure/flow based on other setpoints if present
        flow_setpoint = setpoints.get("flow", state.get("flow", 10.0))
        new_state["flow"] = flow_setpoint + rng.uniform(-noise_level * 0.1, noise_level * 0.1)
        
        # Compute derived values
        new_state["energy_rate"] = (new_state["temperature"] * 0.1 + 
                                   new_state["flow"] * 0.5 + 
                                   rng.uniform(0, 0.5))
        
        return new_state

    @staticmethod
    def compute_kpis(
        timeseries: List[Dict[str, Any]],
        scenario: ScenarioConfig
    ) -> Dict[str, float]:
        """
        Compute KPIs from a completed timeseries.
        """
        if not timeseries:
            return {}

        avg_temp = sum(s["temperature"] for s in timeseries) / len(timeseries)
        total_energy = sum(s["energy_rate"] for s in timeseries)
        avg_flow = sum(s["flow"] for s in timeseries) / len(timeseries)
        
        # Yield formula from scenario config (simplified)
        # S-NORMAL might have higher yield than S-DRIFT
        yield_base = scenario.parameters.get("yield_base", 95.0)
        temp_opt = scenario.parameters.get("temp_optimal", 70.0)
        temp_penalty = sum(abs(s["temperature"] - temp_opt) for s in timeseries) / len(timeseries)
        
        yield_pct = max(0, min(100, yield_base - temp_penalty * 0.5))
        
        # Quality deviation: count steps where temp > upper_bound
        quality_limit = scenario.parameters.get("quality_limit", 90.0)
        deviations = sum(1 for s in timeseries if s["temperature"] > quality_limit)
        
        return {
            "energy_kwh": total_energy,
            "yield_pct": yield_pct,
            "quality_deviation_count": float(deviations),
            "avg_temperature": avg_temp,
            "avg_flow": avg_flow
        }

    @classmethod
    def simulate_run(
        cls,
        scenario: ScenarioConfig,
        horizon: int,
        seed: int,
        setpoints: Optional[Dict[str, float]] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, float]]:
        """
        Simulate a full run for a fixed horizon.
        """
        if setpoints is None:
            setpoints = {"temperature": 70.0, "flow": 12.0} # Default
            
        current_state = scenario.initial_state.copy()
        timeseries = []
        
        for i in range(horizon):
            current_state = cls.simulate_step(current_state, setpoints, scenario, i, seed)
            timeseries.append({"step": i, **current_state})
            
        kpis = cls.compute_kpis(timeseries, scenario)
        return timeseries, kpis
