import os
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from .simulator import simulator
from ..models.schemas import OTConfig
from asyncua import Client, ua

class OPCUAClient:
    def __init__(self):
        self.is_simulated = os.environ.get("FEATURE_SIMULATED_OPCUA", "true").lower() == "true"
        self.client: Optional[Client] = None
        self.config: Optional[OTConfig] = None

    async def connect(self, config: OTConfig):
        self.config = config
        if self.is_simulated:
            return True
        
        try:
            self.client = Client(url=config.endpoint_url)
            # Security policy setup would go here
            await self.client.connect()
            return True
        except Exception:
            return False

    async def disconnect(self):
        if self.is_simulated:
            return
        if self.client:
            await self.client.disconnect()

    async def read_nodes(self, tag_map: Dict[str, str]) -> Dict[str, float]:
        if self.is_simulated:
            # Map human readable tags to simulated nodes
            return simulator.read_nodes(list(tag_map.values()))
        
        if not self.client:
            return {}
        
        results = {}
        for key, node_id in tag_map.items():
            try:
                node = self.client.get_node(node_id)
                val = await node.get_value()
                results[node_id] = val
            except Exception:
                results[node_id] = 0.0
        return results

    async def write_nodes(self, tag_dict: Dict[str, float]) -> Tuple[bool, str]:
        if self.is_simulated:
            ok = simulator.write_nodes(tag_dict)
            return ok, "ok" if ok else "simulator_fail"
        
        if not self.client:
            return False, "not_connected"
            
        try:
            for node_id, value in tag_dict.items():
                node = self.client.get_node(node_id)
                # Determine variant type if needed, but asyncua often handles floats
                await node.set_value(ua.DataValue(ua.Variant(value, ua.VariantType.Float)))
            return True, "ok"
        except Exception as e:
            return False, str(e)

    async def read_alarms(self, alarm_nodes: List[str]) -> List[str]:
        if self.is_simulated:
            vals = simulator.read_nodes(alarm_nodes)
            return [node for node, val in vals.items() if val > 0]
        
        if not self.client:
            return []
            
        active_alarms = []
        for node_id in alarm_nodes:
            try:
                node = self.client.get_node(node_id)
                val = await node.get_value()
                if val:
                    active_alarms.append(node_id)
            except Exception:
                pass
        return active_alarms

    async def read_back(self, live_setpoints_map: Dict[str, str]) -> Dict[str, float]:
        # Same as read_nodes but specifically for live setpoints
        return await self.read_nodes(live_setpoints_map)

opcua_client = OPCUAClient()
