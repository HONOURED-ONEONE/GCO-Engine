from app.api.utils.io import read_json, write_json, REGISTRY_FILE

def set_optimization_mode(mode: str):
    if mode == "sustainability_first":
        weights = {"energy": 0.6, "quality": 0.25, "yield": 0.15}
    else:  # production_first
        weights = {"energy": 0.25, "quality": 0.35, "yield": 0.40}
    
    registry = read_json(REGISTRY_FILE)
    registry["last_mode"] = mode
    registry["last_mode_weights"] = weights
    write_json(REGISTRY_FILE, registry)
    
    return mode, weights

def get_current_weights():
    registry = read_json(REGISTRY_FILE)
    return registry.get("last_mode_weights", {"energy": 0.6, "quality": 0.25, "yield": 0.15})
