import os
import yaml
from typing import Dict, Optional
from ..models.schemas import ScenarioConfig

class ScenarioManager:
    def __init__(self, scenarios_dir: str):
        self.scenarios_dir = scenarios_dir
        self.scenarios: Dict[str, ScenarioConfig] = {}
        self.reload_scenarios()

    def reload_scenarios(self):
        if not os.path.exists(self.scenarios_dir):
            os.makedirs(self.scenarios_dir, exist_ok=True)
            return

        for filename in os.listdir(self.scenarios_dir):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                path = os.path.join(self.scenarios_dir, filename)
                with open(path, "r") as f:
                    try:
                        data = yaml.safe_load(f)
                        scenario = ScenarioConfig(**data)
                        self.scenarios[scenario.id] = scenario
                    except Exception as e:
                        print(f"Error loading scenario {filename}: {e}")

    def get_scenario(self, scenario_id: str) -> Optional[ScenarioConfig]:
        return self.scenarios.get(scenario_id)

    def list_scenarios(self):
        return list(self.scenarios.keys())

# Global instance for the service
scenarios_dir = os.getenv("SCENARIOS_DIR", "/app/twin/scenarios")
# For local testing, fallback to relative path if /app/twin/scenarios doesn't exist
if not os.path.exists(scenarios_dir):
    scenarios_dir = "twin/scenarios"

manager = ScenarioManager(scenarios_dir)
