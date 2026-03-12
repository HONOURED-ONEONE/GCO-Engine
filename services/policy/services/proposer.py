from ..models.schemas import CostShapingDelta, CorridorDelta

def propose_cost_shaping(summary: dict, weights_default: dict, trust_score: float, allow: bool):
    if not allow or summary["n"] < 2:
        return None
        
    energy_trend = summary.get("energy_trend", 0)
    q_viol = summary.get("quality_violations", 0)
    
    weights = dict(weights_default)
    clamp = 0.1 * trust_score
    
    # If energy improved and stable quality, shift weight toward energy
    if energy_trend < -0.01 and q_viol == 0:
        weights["energy"] = min(1.0, weights.get("energy", 0.33) + clamp)
        weights["quality"] = max(0.0, weights.get("quality", 0.34) - clamp/2)
        weights["yield"] = max(0.0, weights.get("yield", 0.33) - clamp/2)
    elif q_viol > 0:
        weights["quality"] = min(1.0, weights.get("quality", 0.34) + clamp)
        weights["energy"] = max(0.0, weights.get("energy", 0.33) - clamp/2)
        weights["yield"] = max(0.0, weights.get("yield", 0.33) - clamp/2)
        
    # Renormalize
    tot = sum(weights.values())
    for k in weights:
        weights[k] = round(weights[k] / tot, 3)
        
    return CostShapingDelta(weights=weights, clamp={"per_obj": 0.1})

def propose_corridor_delta(summary: dict, restraints: bool, allow: bool):
    if not allow or summary["n"] < 2:
        return None
        
    energy_trend = summary.get("energy_trend", 0)
    q_viol = summary.get("quality_violations", 0)
    yield_mean = summary.get("yield_mean", 100)
    
    delta = CorridorDelta()
    changed = False
    
    if energy_trend <= -0.03 and q_viol == 0:
        delta.temperature_upper = -0.5
        changed = True
    elif yield_mean < 85 and q_viol == 0:
        delta.flow_upper = 0.2
        changed = True
    elif q_viol > 0 and not restraints:
        delta.temperature_upper = 0.5
        changed = True
        
    if changed:
        return delta
    return None

def build_proposal(delta: dict, delta_type: str, evidence: dict, confidence: float):
    return {
        "subject": "corridor",
        "delta": {"type": delta_type, "payload": delta},
        "evidence": evidence,
        "confidence": confidence
    }
