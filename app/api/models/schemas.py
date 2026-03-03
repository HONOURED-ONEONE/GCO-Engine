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
    marl_proposal_created: bool
    proposal_id: Optional[str] = None

class KPIItem(BaseModel):
    batch_id: str
    energy_kwh: float
    yield_pct: float
    quality_deviation: bool
    ingested_at: str
    anomaly_flag: bool
    hash: str

class KPIRecentResponse(BaseModel):
    items: List[KPIItem]
    count: int

class CorridorDelta(BaseModel):
    temperature_upper: Optional[float] = 0.0
    temperature_lower: Optional[float] = 0.0
    flow_upper: Optional[float] = 0.0
    flow_lower: Optional[float] = 0.0

class ProposalEvidence(BaseModel):
    summary: str
    kpi_window: List[str]
    metrics: Dict[str, float]
    confidence: float

class CorridorProposeRequest(BaseModel):
    delta: Dict[str, float]
    evidence: ProposalEvidence

class CorridorProposal(BaseModel):
    id: str
    status: Literal["pending", "approved", "rejected"]
    delta: Dict[str, float]
    evidence: ProposalEvidence
    created_at: str
    decided_at: Optional[str] = None
    decided_by: Optional[str] = None
    notes: Optional[str] = None

class CorridorProposeResponse(BaseModel):
    proposal_id: str
    status: str

class CorridorProposalsResponse(BaseModel):
    items: List[CorridorProposal]

class CorridorApproveRequest(BaseModel):
    proposal_id: str
    decision: Literal["approve", "reject"]
    notes: Optional[str] = None

class CorridorApproveResponse(BaseModel):
    status: str
    new_version: Optional[str] = None
    active_bounds: Optional[Dict[str, Dict[str, float]]] = None
    cache_invalidation: List[str] = []
    message: str

class CorridorVersionResponse(BaseModel):
    active_version: str
    bounds: Dict[str, Dict[str, float]]
    history: List[Dict]

class AuditEntry(BaseModel):
    at: str
    type: str
    data: Dict[str, Any]

class CorridorAuditResponse(BaseModel):
    items: List[AuditEntry]

class CorridorDiffResponse(BaseModel):
    from_version: str
    to_version: str
    changes: Dict[str, Dict[str, Any]]
    impact_hints: Dict[str, str]
