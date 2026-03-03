from typing import Dict, List, Literal, Optional, Any
from pydantic import BaseModel
from datetime import datetime

class ModeSetRequest(BaseModel):
    mode: str
    operator_id: Optional[str] = "stubbed-operator"

class ModeSetResponse(BaseModel):
    mode: str
    weights: Dict[str, float]
    changed: bool
    changed_at: datetime
    message: str

class ModeCurrentResponse(BaseModel):
    mode: str
    weights: Dict[str, float]
    changed_at: datetime
    operator_id: str

class ModePolicyItem(BaseModel):
    id: str
    label: str
    weights: Dict[str, float]
    description: str

class ModePolicyResponse(BaseModel):
    allowed_modes: List[ModePolicyItem]
    notes: str

class OptimizeRecommendRequest(BaseModel):
    batch_id: str
    ts: str
    hints: Optional[Dict[str, Any]] = None

class OptimizeRecommendResponse(BaseModel):
    setpoints: Dict[str, float]
    within_bounds: bool
    objective_weights: Dict[str, float]
    objective_breakdown: Dict[str, float]
    constraints: Dict[str, List[float]]
    nudge_applied: Dict[str, float]
    compute_ms: int
    rationale: str

class PreviewPoint(BaseModel):
    ts: str
    state: Dict[str, float]
    setpoints: Dict[str, float]
    objective_total: float
    bounds: Dict[str, List[float]]

class OptimizePreviewResponse(BaseModel):
    horizon: int
    step_sec: int
    points: List[PreviewPoint]
    compute_ms: int
    note: str

class CacheStats(BaseModel):
    bounds_hits: int
    bounds_misses: int
    ttl_sec: int

class OptimizeHealthResponse(BaseModel):
    uptime_sec: int
    calls_total: int
    cache: CacheStats
    latency_ms_p50: int
    latency_ms_p95: int

class KPIIngestRequest(BaseModel):
    batch_id: str
    energy_kwh: float
    yield_pct: float
    quality_deviation: bool

class KPIIngestResponse(BaseModel):
    ok: bool
    anomaly_flag: bool
    message: str

class CorridorProposeRequest(BaseModel):
    delta: Dict[str, float]
    evidence: str

class CorridorProposeResponse(BaseModel):
    proposal_id: str
    status: Literal["pending", "rejected", "approved"]

class CorridorApproveRequest(BaseModel):
    proposal_id: str
    decision: Literal["approve", "reject"]
    notes: Optional[str] = None

class CorridorApproveResponse(BaseModel):
    status: str
    new_version: Optional[str] = None

class CorridorVersionResponse(BaseModel):
    active_version: str
    bounds: Dict[str, Dict[str, float]]
    history: List[Dict]
