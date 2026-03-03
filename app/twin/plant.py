import numpy as np
import time
import uuid

class BatchPlant:
    def __init__(self, scenario_config=None, seed=42):
        self.rng = np.random.default_rng(seed)
        self.dt = scenario_config.get("dt", 1.0)
        self.alpha = scenario_config.get("alpha", 0.1)
        self.beta = scenario_config.get("beta", 0.05)
        self.gamma = scenario_config.get("gamma", 0.2)
        
        # State
        self.temperature = 25.0
        self.flow = 0.0
        self.ambient_temp = scenario_config.get("ambient_temp", 25.0)
        
        # Setpoints (Inputs)
        self.u_heat = 0.0
        self.u_valve = 0.0
        
        # Batch context
        self.batch_id = ""
        self.phase = "IDLE" # IDLE, WARM_UP, HOLD, RAMP_DOWN
        self.step_count = 0
        self.max_steps = scenario_config.get("max_steps", 120)
        
        # Performance
        self.energy_kwh = 0.0
        self.yield_proxy = 0.0
        self.quality_violations = 0
        
        # Phase config
        self.phases = scenario_config.get("phases", {
            "WARM_UP": {"duration": 20, "target_temp": 60.0, "target_flow": 5.0},
            "HOLD": {"duration": 80, "target_temp": 60.0, "target_flow": 5.0},
            "RAMP_DOWN": {"duration": 20, "target_temp": 25.0, "target_flow": 0.0}
        })
        self.current_phase_idx = 0
        self.phase_list = ["WARM_UP", "HOLD", "RAMP_DOWN"]

    def start_batch(self, batch_id=None):
        self.batch_id = batch_id or f"B{uuid.uuid4().hex[:4].upper()}"
        self.temperature = 25.0
        self.flow = 0.0
        self.energy_kwh = 0.0
        self.yield_proxy = 0.0
        self.quality_violations = 0
        self.step_count = 0
        self.current_phase_idx = 0
        self.phase = self.phase_list[0]
        return self.batch_id

    def step(self, u_heat_sp, u_valve_sp):
        self.u_heat = u_heat_sp
        self.u_valve = u_valve_sp
        
        # Process Noise
        w_T = self.rng.normal(0, 0.05)
        w_F = self.rng.normal(0, 0.02)
        
        # Model: T[k+1] = T[k] + alpha*(u_heat[k] - beta*(T[k]-T_amb[k])) + w_T
        dT = self.alpha * (self.u_heat - self.beta * (self.temperature - self.ambient_temp)) + w_T
        self.temperature += dT
        
        # Model: F[k+1] = F[k] + gamma*(u_valve[k] - F[k]) + w_F
        dF = self.gamma * (self.u_valve - self.flow) + w_F
        self.flow += dF
        
        # KPI accumulation
        self.energy_kwh += (self.u_heat * 0.5 + self.u_valve * 0.1) * (self.dt / 3600.0) # Dummy energy calc
        
        # Check constraints for quality
        target = self.phases[self.phase]
        if self.phase == "HOLD":
            if abs(self.temperature - target["target_temp"]) > 2.0:
                self.quality_violations += 1
            self.yield_proxy += self.flow * 0.01

        self.step_count += 1
        
        # Phase transitions
        phase_config = self.phases[self.phase]
        if self.step_count % phase_config["duration"] == 0:
            self.current_phase_idx += 1
            if self.current_phase_idx < len(self.phase_list):
                self.phase = self.phase_list[self.current_phase_idx]
            else:
                self.phase = "IDLE"
        
        return {
            "batch_id": self.batch_id,
            "step": self.step_count,
            "phase": self.phase,
            "temperature": self.temperature,
            "flow": self.flow,
            "energy_kwh": self.energy_kwh,
            "quality_violations": self.quality_violations
        }

    def get_status(self):
        return {
            "batch_id": self.batch_id,
            "phase": self.phase,
            "temperature": self.temperature,
            "flow": self.flow,
            "u_heat": self.u_heat,
            "u_valve": self.u_valve,
            "step": self.step_count
        }
