import time
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional

def check_armed(armed_until_iso: Optional[str], now: float) -> bool:
    if not armed_until_iso:
        return False
    try:
        armed_until = datetime.fromisoformat(armed_until_iso).timestamp()
        return now < armed_until
    except Exception:
        return False

def check_bounds(setpoints: Dict[str, float], bounds: Dict[str, Dict[str, float]]) -> Tuple[bool, List[str]]:
    violations = []
    for key, value in setpoints.items():
        if key in bounds:
            b = bounds[key]
            if value < b.get("min", -float('inf')) or value > b.get("max", float('inf')):
                violations.append(f"{key}: {value} out of [{b.get('min')}, {b.get('max')}]")
    return len(violations) == 0, violations

def check_alarms(active_alarms: List[str], blocklist: List[str]) -> List[str]:
    # active_alarms are node_ids
    # blocklist elements are usually also node_ids or strings that we should match
    blocking = []
    for alarm in active_alarms:
        for blocked in blocklist:
            if blocked in alarm: # Simple substring match for flexibility
                blocking.append(alarm)
    return list(set(blocking))

def check_rate_limit(last_write_ts_iso: Optional[str], min_interval_sec: int, now: float) -> Tuple[bool, float]:
    if not last_write_ts_iso:
        return True, 0.0
    try:
        last_write_ts = datetime.fromisoformat(last_write_ts_iso).timestamp()
        elapsed = now - last_write_ts
        return elapsed >= min_interval_sec, elapsed
    except Exception:
        return True, 0.0

def confirm_readback(requested: Dict[str, float], readback: Dict[str, float], tolerance_map: Dict[str, float], tag_map_live: Dict[str, str]) -> Tuple[bool, Dict[str, float]]:
    # tag_map_live maps human-friendly key -> node_id
    # readback is node_id -> value
    # requested is human-friendly key -> value
    diffs = {}
    ok = True
    for key, req_val in requested.items():
        node_id = tag_map_live.get(key)
        if node_id in readback:
            rb_val = readback[node_id]
            diff = abs(req_val - rb_val)
            diffs[key] = diff
            tolerance = tolerance_map.get(key, 0.1)
            if diff > tolerance:
                ok = False
        else:
            ok = False
            diffs[key] = float('nan')
    return ok, diffs
