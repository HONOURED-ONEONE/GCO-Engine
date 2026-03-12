from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import time
import os
import uuid
from ..models.schemas import OTConfig, ArmRequest, WriteRequest, OTStatus, HealthStatus
from ..services.state import state_manager
from ..services.opcua_client import opcua_client
from ..services.interlocks import (
    check_armed, check_bounds, check_alarms, check_rate_limit, confirm_readback
)
from ..services.commissioning import verify_readiness, COMMISSIONING_MODE
from ..clients.governance_client import governance_client
from ..security.rbac import require_role
from ..utils.metrics import metrics

router = APIRouter(prefix="/ot")

FEATURE_GUARDED = os.environ.get("FEATURE_GUARDED", "false").lower() == "true"

@router.post("/config/set")
async def set_config(config: OTConfig, claims: dict = Depends(require_role(["Admin"]))):
    state_manager.save_config(config.dict())
    ok = await opcua_client.connect(config)
    
    state_updates = {"connector_state": "connected" if ok else "disconnected"}
    if opcua_client.is_simulated:
        state_updates["connector_state"] = "simulated"
    
    state_manager.update_state(state_updates)
    
    if not ok:
        metrics.opcua_connect_failures += 1
        
    await governance_client.post_audit(
        "ot_config_set", 
        {"endpoint_url": config.endpoint_url, "ok": ok}, 
        claims.get("sub", "admin")
    )
    
    return config

@router.get("/config")
async def get_config(claims: dict = Depends(require_role(["Engineer", "Admin"]))):
    config = state_manager.get_config()
    if not config:
        raise HTTPException(status_code=404, detail="Config not set")
    # Sanitize: Remove password
    if "auth" in config:
        config["auth"]["password"] = "********"
    return config

@router.post("/arm")
async def arm(req: ArmRequest, claims: dict = Depends(require_role(["Operator", "Engineer", "Admin"]))):
    now = datetime.utcnow()
    expires_at = now + timedelta(seconds=req.duration_sec)
    
    state_manager.update_state({
        "armed_until": expires_at.isoformat(),
        "batch_id": req.batch_id
    })
    
    await governance_client.post_audit(
        "ot_armed", 
        {"batch_id": req.batch_id, "expires_at": expires_at.isoformat(), "notes": req.notes}, 
        claims.get("sub", "user")
    )
    
    return {"status": "armed", "expires_at": expires_at}

@router.post("/disarm")
async def disarm(claims: dict = Depends(require_role(["Operator", "Engineer", "Admin"]))):
    state_manager.update_state({"armed_until": None})
    
    await governance_client.post_audit(
        "ot_disarmed", 
        {}, 
        claims.get("sub", "user")
    )
    
    return {"status": "disarmed"}

@router.post("/shadow/write")
async def shadow_write(req: WriteRequest, claims: dict = Depends(require_role(["Operator", "Engineer", "Admin"]))):
    if COMMISSIONING_MODE:
        return {"ok": False, "reason": "commissioning_mode_active"}
    start_time = time.time()
    config_dict = state_manager.get_config()
    if not config_dict:
        raise HTTPException(status_code=400, detail="OT service not configured")
    config = OTConfig(**config_dict)
    
    tag_map = {}
    for key, value in req.setpoints.items():
        if key in config.tag_map.shadow_setpoints:
            tag_map[config.tag_map.shadow_setpoints[key]] = value

    await governance_client.post_audit(
        "ot_shadow_write_attempt", 
        {"setpoints": req.setpoints, "notes": req.notes}, 
        claims.get("sub", "user")
    )
    
    ok, details = await opcua_client.write_nodes(tag_map)
    
    result = "ok" if ok else "fail"
    await governance_client.post_audit(
        f"ot_shadow_write_{result}", 
        {"setpoints": req.setpoints, "details": details}, 
        claims.get("sub", "user")
    )
    
    state_manager.update_state({
        "last_write": {
            "ts": datetime.utcnow().isoformat(),
            "type": "shadow",
            "result": result,
            "by": claims.get("sub", "user"),
            "details": {"msg": details}
        }
    })
    
    metrics.record_call((time.time() - start_time) * 1000)
    if not ok:
        metrics.write_failures += 1
        
    return {"ok": ok, "details": details}

@router.post("/guarded/write")
async def guarded_write(req: WriteRequest, claims: dict = Depends(require_role(["Engineer", "Admin"]))):
    if COMMISSIONING_MODE:
        return {"ok": False, "reason": "commissioning_mode_active"}
    start_time = time.time()
    if not FEATURE_GUARDED:
        return {"ok": False, "reason": "guarded_disabled"}
    
    config_dict = state_manager.get_config()
    if not config_dict:
        raise HTTPException(status_code=400, detail="OT service not configured")
    config = OTConfig(**config_dict)
    state = state_manager.get_state()
    
    await governance_client.post_audit(
        "ot_guarded_write_attempt", 
        {"setpoints": req.setpoints, "notes": req.notes}, 
        claims.get("sub", "user")
    )

    # 1. Armed check
    now_ts = time.time()
    if not check_armed(state.get("armed_until"), now_ts):
        return {"ok": False, "reason": "not_armed"}

    # 2. Rate limit check
    last_write = state.get("last_write")
    last_ts = last_write["ts"] if last_write else None
    rl_ok, elapsed = check_rate_limit(last_ts, config.min_write_interval_sec, now_ts)
    if not rl_ok:
        return {"ok": False, "reason": "rate_limit", "seconds_remaining": config.min_write_interval_sec - elapsed}

    # 3. Alarms check
    active_alarms = await opcua_client.read_alarms(config.tag_map.alarms)
    blocking_alarms = check_alarms(active_alarms, config.alarm_blocklist)
    if blocking_alarms:
        return {"ok": False, "reason": "alarms_blocking", "alarms": blocking_alarms}

    # 4. Corridor bounds check
    gov_active = await governance_client.get_active()
    bounds = gov_active.get("bounds", {})
    bounds_ok, violations = check_bounds(req.setpoints, bounds)
    if not bounds_ok:
        return {"ok": False, "reason": "bounds_violation", "violations": violations}

    last_good = state.get("last_good_setpoint", {})
    
    # 5. Write to live
    tag_map = {config.tag_map.live_setpoints[k]: v for k, v in req.setpoints.items() if k in config.tag_map.live_setpoints}
    ok, details = await opcua_client.write_nodes(tag_map)
    
    if not ok:
        metrics.write_failures += 1
        await governance_client.post_audit("ot_guarded_write_fail", {"reason": "opcua_error", "details": details}, claims.get("sub"))
        return {"ok": False, "reason": "opcua_error", "details": details}

    # 6. Read-back confirmation
    readback = await opcua_client.read_back(config.tag_map.live_setpoints)
    rb_ok, diffs = confirm_readback(req.setpoints, readback, config.readback_tolerance, config.tag_map.live_setpoints)
    
    if not rb_ok:
        metrics.write_failures += 1
        revert_tags = {config.tag_map.live_setpoints[k]: v for k, v in last_good.items() if k in config.tag_map.live_setpoints}
        revert_ok, rev_details = await opcua_client.write_nodes(revert_tags)
        metrics.reverts += 1
        
        await governance_client.post_audit("ot_guarded_write_fail", {"reason": "readback_mismatch", "diffs": diffs}, claims.get("sub"))
        await governance_client.post_audit(f"ot_guarded_revert_{'ok' if revert_ok else 'fail'}", {"details": rev_details}, claims.get("sub"))
        
        return {"ok": False, "reason": "readback_mismatch", "diffs": diffs, "revert_status": "ok" if revert_ok else "fail"}

    # Success
    state_manager.update_state({
        "last_write": {
            "ts": datetime.utcnow().isoformat(),
            "type": "guarded",
            "result": "ok",
            "by": claims.get("sub", "user")
        },
        "last_good_setpoint": req.setpoints,
        "last_readback": readback
    })
    
    await governance_client.post_audit("ot_guarded_write_ok", {"setpoints": req.setpoints}, claims.get("sub"))
    metrics.record_call((time.time() - start_time) * 1000)
    
    return {"ok": True}

@router.post("/rollback")
async def rollback(claims: dict = Depends(require_role(["Admin"]))):
    state = state_manager.get_state()
    last_good = state.get("last_good_setpoint", {})
    if not last_good:
        raise HTTPException(status_code=400, detail="No last good setpoint to rollback to")
    
    config_dict = state_manager.get_config()
    if not config_dict:
        raise HTTPException(status_code=400, detail="OT service not configured")
    config = OTConfig(**config_dict)
    
    revert_tags = {config.tag_map.live_setpoints[k]: v for k, v in last_good.items() if k in config.tag_map.live_setpoints}
    ok, details = await opcua_client.write_nodes(revert_tags)
    
    await governance_client.post_audit(
        "ot_manual_rollback", 
        {"setpoints": last_good, "ok": ok, "details": details}, 
        claims.get("sub", "admin")
    )
    
    if not ok:
        raise HTTPException(status_code=500, detail=f"Rollback failed: {details}")
        
    return {"ok": True, "message": "Rollback successful", "setpoints": last_good}

@router.post("/commissioning/verify")
async def commissioning_verify(claims: dict = Depends(require_role(["Engineer", "Admin"]))):
    return await verify_readiness()

@router.get("/status", response_model=OTStatus)
async def get_status(claims: dict = Depends(require_role(["Operator", "Engineer", "Admin"]))):
    state = state_manager.get_state()
    config_dict = state_manager.get_config() or {}
    config = OTConfig(**config_dict) if config_dict else None
    
    now = time.time()
    armed = check_armed(state.get("armed_until"), now)
    
    last_write = state.get("last_write")
    last_ts = last_write["ts"] if last_write else None
    min_int = config.min_write_interval_sec if config else 10
    rl_ok, elapsed = check_rate_limit(last_ts, min_int, now)
    
    active_alarms = []
    blocking = []
    if config:
        active_alarms = await opcua_client.read_alarms(config.tag_map.alarms)
        blocking = check_alarms(active_alarms, config.alarm_blocklist)

    return {
        "mode": "guarded" if FEATURE_GUARDED else "shadow",
        "armed": armed,
        "window_expires_at": state.get("armed_until"),
        "connector_state": state.get("connector_state", "disconnected"),
        "last_write": last_write,
        "last_readback": state.get("last_readback"),
        "rate_limit": {
            "min_interval_sec": min_int,
            "ok": rl_ok,
            "seconds_since_last": elapsed
        },
        "alarms_blocking": blocking
    }

@router.get("/alarms")
async def get_alarms(claims: dict = Depends(require_role(["Operator", "Engineer", "Admin"]))):
    config_dict = state_manager.get_config()
    if not config_dict:
        return {"active": [], "blocklist": []}
    config = OTConfig(**config_dict)
    
    active = await opcua_client.read_alarms(config.tag_map.alarms)
    return {
        "active": active,
        "blocklist": config.alarm_blocklist,
        "blocking": check_alarms(active, config.alarm_blocklist)
    }

@router.get("/health", response_model=HealthStatus)
async def get_health(claims: dict = Depends(require_role(["Engineer", "Admin"]))):
    return metrics.get_health()
