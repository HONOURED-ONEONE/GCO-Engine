from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union

class ContextModel(BaseModel):
    corridor_version: str
    mode: str

class StrategyModel(BaseModel):
    allow_cost_shaping: bool = True
    allow_corridor_delta: bool = True
    counterfactuals: bool = True

class KPIItem(BaseModel):
    batch_id: str
    energy_kwh: float
    yield_pct: float
    quality_deviation: bool
    at: str

class KPIWindow(BaseModel):
    items: Optional[List[KPIItem]] = None
    n: int = 5

class MaybeProposeRequest(BaseModel):
    window: Optional[KPIWindow] = None
    context: ContextModel
    strategy: StrategyModel
    class Config:
        extra = 'forbid'

class CostShapingDelta(BaseModel):
    weights: Dict[str, float]
    clamp: Dict[str, float]

class CorridorDelta(BaseModel):
    temperature_upper: Optional[float] = None
    temperature_lower: Optional[float] = None
    flow_upper: Optional[float] = None
    flow_lower: Optional[float] = None

class MaybeProposeResponse(BaseModel):
    proposed: bool
    proposal_id: Optional[str]
    delta: Optional[Dict[str, Any]]
    uncertainty: float = Field(ge=0.0, le=1.0)
    restraint: bool
    confidence: float = Field(ge=0.5, le=0.9)
    evidence: Dict[str, Any]

class ReplayModel(BaseModel):
    versions_decay: Dict[str, float]

class TrainRequest(BaseModel):
    context: ContextModel
    epochs: int = 1
    replay: Optional[ReplayModel] = None

class ActivateResponse(BaseModel):
    ok: bool
    active: str

class PolicyItem(BaseModel):
    id: str
    trained_at: Optional[str] = None
    notes: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None

class ListResponse(BaseModel):
    items: List[Dict[str, Any]]

class HealthResponse(BaseModel):
    uptime_sec: int
    calls_total: int
    p95_ms: float
    store_sizes: int
    last_proposal_id: Optional[str]
    last_confidence: Optional[float]
    uncertainty_avg: float

class PolicyExperiencesResponse(BaseModel):
    items: List[Dict[str, Any]]
