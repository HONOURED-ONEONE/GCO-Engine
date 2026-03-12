from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union, Any
from datetime import datetime

class OTAuth(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None

class OTSecurity(BaseModel):
    policy: str = "None"
    mode: str = "Sign"
    cert_path: Optional[str] = None
    key_path: Optional[str] = None

class OTTagMap(BaseModel):
    sensors: Dict[str, str]
    shadow_setpoints: Dict[str, str]
    live_setpoints: Dict[str, str]
    alarms: List[str]

class OTConfig(BaseModel):
    endpoint_url: str
    security: OTSecurity
    auth: OTAuth
    tag_map: OTTagMap
    alarm_blocklist: List[str]
    min_write_interval_sec: int = 10
    readback_tolerance: Dict[str, float]

class ArmRequest(BaseModel):
    batch_id: str
    duration_sec: int = 120
    notes: Optional[str] = None

class WriteRequest(BaseModel):
    setpoints: Dict[str, float]
    notes: Optional[str] = None

class OTWriteResult(BaseModel):
    ts: datetime
    type: str  # "shadow" | "guarded"
    result: str  # "ok" | "fail"
    by: str
    details: Optional[Dict[str, Any]] = None

class OTStatus(BaseModel):
    mode: str  # "shadow" | "guarded"
    armed: bool
    window_expires_at: Optional[datetime] = None
    connector_state: str  # "connected" | "disconnected" | "simulated"
    last_write: Optional[OTWriteResult] = None
    last_readback: Optional[Dict[str, float]] = None
    rate_limit: Dict[str, Any]
    alarms_blocking: List[str]

class HealthStatus(BaseModel):
    uptime_sec: float
    calls_total: int
    p50_latency_ms: float
    p95_latency_ms: float
    opcua_connect_failures: int
    write_failures: int
    reverts: int
    audit_failures: int
