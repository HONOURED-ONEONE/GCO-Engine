import numpy as np
import pandas as pd
from typing import List, Dict

class ROICalculator:
    def __init__(self, energy_price=0.15, co2_factor=0.4):
        self.energy_price = energy_price
        self.co2_factor = co2_factor # kgCO2 per kWh

    def calculate_savings(self, baseline_kpis: List[Dict], shadow_kpis: List[Dict]):
        if not baseline_kpis or not shadow_kpis:
             return {"error": "Missing KPI data for comparison"}
             
        df_base = pd.DataFrame(baseline_kpis)
        df_shad = pd.DataFrame(shadow_kpis)
        
        base_avg_energy = df_base['energy_kwh'].mean()
        shad_avg_energy = df_shad['energy_kwh'].mean()
        
        delta_energy = base_avg_energy - shad_avg_energy
        delta_cost = delta_energy * self.energy_price
        delta_co2 = delta_energy * self.co2_factor
        
        # Simple bootstrap CI (90%)
        resamples = []
        for _ in range(200):
             sample = df_shad.sample(len(df_shad), replace=True)
             resamples.append(base_avg_energy - sample['energy_kwh'].mean())
        
        ci_low = np.percentile(resamples, 5)
        ci_high = np.percentile(resamples, 95)
        
        return {
            "avg_baseline_kwh": round(base_avg_energy, 2),
            "avg_shadow_kwh": round(shad_avg_energy, 2),
            "delta_kwh_per_batch": round(delta_energy, 2),
            "delta_cost_per_batch": round(delta_cost, 2),
            "delta_co2_per_batch": round(delta_co2, 2),
            "ci_90": [round(ci_low, 2), round(ci_high, 2)],
            "annualized_savings_est": round(delta_cost * 1000, 2) # Assume 1000 batches/yr
        }
