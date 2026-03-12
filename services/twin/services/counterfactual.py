from typing import Dict, Any, List
from .simulator import Simulator
from .scenarios import manager
from ..models.schemas import CounterfactualRequest, CounterfactualResponse

class CounterfactualEngine:
    @staticmethod
    def run_counterfactual(req: CounterfactualRequest) -> CounterfactualResponse:
        scenario = manager.get_scenario(req.scenario_id)
        if not scenario:
            raise ValueError(f"Scenario {req.scenario_id} not found")

        # 1. Baseline simulation
        # Use default horizon of 60 for comparison
        horizon = 60
        baseline_timeseries, baseline_kpis = Simulator.simulate_run(scenario, horizon, req.seed)

        # 2. Adjusted simulation
        # Clone scenario and apply deltas
        adj_scenario = scenario.copy(deep=True)
        
        # Apply corridor deltas (simulated as parameter shifts)
        for key, delta in req.corridor_delta.items():
            if key in adj_scenario.parameters:
                adj_scenario.parameters[key] += delta
            # If delta affects quality limit
            if key == "temperature_upper":
                adj_scenario.parameters["quality_limit"] += delta

        # Apply weight deltas (simulated as KPI scoring shift)
        # Note: weights don't change the physics, just the interpretation
        # For this simplified twin, we mainly report the delta in physical KPIs

        adj_timeseries, adj_kpis = Simulator.simulate_run(adj_scenario, horizon, req.seed)

        # 3. Compute deltas
        energy_delta_pct = (adj_kpis["energy_kwh"] / baseline_kpis["energy_kwh"] - 1.0) * 100
        yield_delta = adj_kpis["yield_pct"] - baseline_kpis["yield_pct"]
        
        risk_quality = "low"
        if adj_kpis["quality_deviation_count"] > baseline_kpis["quality_deviation_count"]:
            risk_quality = "medium"
        if adj_kpis["quality_deviation_count"] > baseline_kpis["quality_deviation_count"] + 5:
            risk_quality = "high"

        return CounterfactualResponse(
            scenario_id=req.scenario_id,
            seed=req.seed,
            metrics={
                "expected_energy_delta_pct": round(energy_delta_pct, 2),
                "yield_delta": round(yield_delta, 2),
                "risk_quality": risk_quality,
                "baseline_kpis": baseline_kpis,
                "adjusted_kpis": adj_kpis
            },
            timeseries=adj_timeseries[:10] # Subset for brevity
        )
