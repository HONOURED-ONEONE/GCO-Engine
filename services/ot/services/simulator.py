import random
import time
from typing import Dict, List, Any

class OTSimulator:
    def __init__(self, seed: int = 4269):
        self.random = random.Random(seed)
        self.tags: Dict[str, float] = {
            "ns=2;s=Sensor.Temperature": 150.0,
            "ns=2;s=Sensor.Flow": 10.0,
            "ns=2;s=SP.Shadow.Temperature": 150.0,
            "ns=2;s=SP.Shadow.Flow": 10.0,
            "ns=2;s=SP.Live.Temperature": 150.0,
            "ns=2;s=SP.Live.Flow": 10.0,
            "ns=2;s=Alarm.OverTemp": 0.0,
            "ns=2;s=Alarm.FlowLow": 0.0,
        }
        self.last_update = time.time()

    def update(self):
        now = time.time()
        dt = now - self.last_update
        self.last_update = now

        # Update sensors to trend towards live setpoints
        # temperature
        target_temp = self.tags.get("ns=2;s=SP.Live.Temperature", 150.0)
        current_temp = self.tags["ns=2;s=Sensor.Temperature"]
        self.tags["ns=2;s=Sensor.Temperature"] += (target_temp - current_temp) * 0.1 * dt + (self.random.random() - 0.5) * 0.2
        
        # flow
        target_flow = self.tags.get("ns=2;s=SP.Live.Flow", 10.0)
        current_flow = self.tags["ns=2;s=Sensor.Flow"]
        self.tags["ns=2;s=Sensor.Flow"] += (target_flow - current_flow) * 0.1 * dt + (self.random.random() - 0.5) * 0.1

        # Alarms
        self.tags["ns=2;s=Alarm.OverTemp"] = 1.0 if self.tags["ns=2;s=Sensor.Temperature"] > 200.0 else 0.0
        self.tags["ns=2;s=Alarm.FlowLow"] = 1.0 if self.tags["ns=2;s=Sensor.Flow"] < 1.0 else 0.0

    def read_nodes(self, nodes: List[str]) -> Dict[str, float]:
        self.update()
        return {node: self.tags.get(node, 0.0) for node in nodes}

    def write_nodes(self, node_values: Dict[str, float]) -> bool:
        self.update()
        for node, value in node_values.items():
            if node in self.tags:
                self.tags[node] = value
        return True

simulator = OTSimulator()
