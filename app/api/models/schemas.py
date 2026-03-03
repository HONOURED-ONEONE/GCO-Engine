from typing import Dict, List, Literal, Optional
from pydantic import BaseModel

class ModeSetRequest(BaseModel):
    mode: Literal["sustainability_first", "production_first"]

class ModeSetResponse(BaseModel):
    mode: str
    weights: Dict[str, float]

class OptimizeRecommendRequest(BaseModel):
    batch_id: str
    ts: str

class OptimizeRecommendResponse(BaseModel):
    setpoints: Dict[str, float]
    rationale: str
    within_bounds: bool
    objective_weights: Dict[str, float]

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
