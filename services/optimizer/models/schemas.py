from typing import Dict, List, Optional, Any
from pydantic import BaseModel

class OptimizeRecommendRequest(BaseModel):
    batch_id: str
    ts: str
    hints: Optional[Dict[str, Any]] = None
    write_back: Optional[bool] = False

class OTStatus(BaseModel):
    write_attempted: bool
    success: Optional[bool] = None
    message: Optional[str] = None

class OptimizeRecommendResponse(BaseModel):
    setpoints: Dict[str, float]
    within_bounds: bool
    objective_weights: Dict[str, float]
    objective_breakdown: Optional[Dict[str, float]] = None
    constraints: Dict[str, Any]
    nudge_applied: Optional[Dict[str, float]] = None
    compute_ms: int
    rationale: str
    fallback_active: Optional[bool] = False
    solver_status: Optional[str] = None
    ot_status: Optional[OTStatus] = None

class PreviewPoint(BaseModel):
    ts: str
    state: Dict[str, float]
    setpoints: Dict[str, float]
    objective_total: Optional[float] = None
    bounds: Dict[str, Any]
    fallback: Optional[bool] = False

class OptimizePreviewResponse(BaseModel):
    horizon: int
    step_sec: int
    points: List[PreviewPoint]
    compute_ms: int
    note: Optional[str] = None

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
    solver: Optional[str] = "CasADi/IPOPT"
    solver_success_rate: Optional[float] = 0.0
