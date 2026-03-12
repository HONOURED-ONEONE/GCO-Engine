import os
from typing import Dict, Any
from .state import state_manager
from .opcua_client import opcua_client
from ..models.schemas import OTConfig

COMMISSIONING_MODE = os.environ.get("COMMISSIONING_MODE", "false").lower() == "true"

async def verify_readiness() -> Dict[str, Any]:
    config_dict = state_manager.get_config()
    if not config_dict:
        return {"ok": False, "reason": "Config not set", "steps": {}}
    
    config = OTConfig(**config_dict)
    steps = {}
    
    # 1. Config validity
    steps["config_valid"] = True
    
    # 2. OPC-UA connectivity
    steps["connectivity"] = await opcua_client.connect(config)
    
    # 3. Tag map completeness (Simple check)
    steps["tag_map"] = all([
        config.tag_map.shadow_setpoints,
        config.tag_map.live_setpoints,
        config.tag_map.alarms
    ])
    
    # 4. Alarm nodes reachable
    try:
        alarms = await opcua_client.read_alarms(config.tag_map.alarms)
        steps["alarms_reachable"] = True
    except:
        steps["alarms_reachable"] = False
        
    # 5. Live tags readable
    try:
        readback = await opcua_client.read_back(config.tag_map.live_setpoints)
        steps["live_readable"] = True
    except:
        steps["live_readable"] = False
        
    # 6. Simulation check
    steps["simulated"] = opcua_client.is_simulated
    
    overall_ok = all([
        steps["config_valid"],
        steps["connectivity"],
        steps["tag_map"],
        steps["alarms_reachable"],
        steps["live_readable"]
    ])
    
    return {
        "ok": overall_ok,
        "commissioning_mode": COMMISSIONING_MODE,
        "steps": steps,
        "details": "Readiness report generated"
    }
