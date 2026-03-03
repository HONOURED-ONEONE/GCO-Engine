import yaml
import os
import asyncio
from app.twin.plant import BatchPlant

SCENARIOS_DIR = "app/twin/scenarios"

class TwinService:
    def __init__(self):
        self.active_session = None
        self.plant = None
        self.scenario = None
        self.opcua_server = None # Placeholder for OPC-UA
        self.running = False
        self.task = None

    def get_scenarios(self):
        scenarios = []
        for f in os.listdir(SCENARIOS_DIR):
            if f.endswith(".yaml"):
                with open(os.path.join(SCENARIOS_DIR, f), 'r') as stream:
                    scenarios.append(yaml.safe_load(stream))
        return scenarios

    async def start_twin(self, scenario_id, seed=4269, batch_count=10, opcua=False):
        if self.running:
            return {"error": "Twin already running"}
        
        scenario_path = os.path.join(SCENARIOS_DIR, f"{scenario_id}.yaml")
        if not os.path.exists(scenario_path):
            return {"error": f"Scenario {scenario_id} not found"}
            
        with open(scenario_path, 'r') as f:
            self.scenario = yaml.safe_load(f)
            
        self.plant = BatchPlant(self.scenario, seed=seed)
        self.active_session = f"tw-{seed}"
        self.running = True
        
        # Start background simulation task if needed
        # For now, we'll just return status. The orchestrator will drive the steps.
        
        return {
            "twin_session_id": self.active_session,
            "status": "running",
            "tags": ["sensors.temperature", "sensors.flow", "setpoints.temperature_shadow", "setpoints.flow_shadow"],
            "note": "Twin ready for shadow mode"
        }

    async def stop_twin(self):
        self.running = False
        self.active_session = None
        return {"status": "stopped"}

    def get_status(self):
        if not self.running:
            return {"status": "stopped"}
        return {
            "status": "running",
            "current_status": self.plant.get_status(),
            "scenario": self.scenario["id"]
        }

twin_service = TwinService()
