from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any

class ScenarioConfig(BaseModel):
    id: str
    name: str
    description: str
    initial_state: Dict[str, float]
    parameters: Dict[str, float]
    disturbance_model: Dict[str, Any]
    kpi_formulas: Dict[str, str]

class TwinStartRequest(BaseModel):
    scenario_id: str
    seed: int = 42

class TwinStartResponse(BaseModel):
    session_id: str
    scenario_id: str
    status: str

class TwinStatusResponse(BaseModel):
    session_id: str
    state: Dict[str, float]
    metrics: Dict[str, float]
    progress: float

class TwinRunRequest(BaseModel):
    scenario_id: str
    horizon: int
    seed: int = 42

class TwinRunResponse(BaseModel):
    scenario_id: str
    seed: int
    timeseries: List[Dict[str, Any]]
    kpis: Dict[str, float]
    summary: Dict[str, Any]

class CounterfactualRequest(BaseModel):
    scenario_id: str
    corridor_delta: Dict[str, float]
    weight_delta: Dict[str, float]
    seed: int = 42

class CounterfactualResponse(BaseModel):
    metrics: Dict[str, Any]
    timeseries: Optional[List[Dict[str, Any]]] = None
    scenario_id: str
    seed: int

class PilotStartRequest(BaseModel):
    pilot_id: str
    scenario_id: str
    mode: str
    horizon_minutes: int
    seed: int = 42

class PilotStartResponse(BaseModel):
    pilot_id: str
    status: str

class PilotHealthResponse(BaseModel):
    pilot_id: str
    uptime_sec: float
    progress: float
    last_step: Optional[Dict[str, Any]] = None

class PilotSnapshotResponse(BaseModel):
    pilot_id: str
    scenario_id: str
    mode: str
    timeseries: List[Dict[str, Any]]
    kpis: List[Dict[str, Any]]
    summary: Dict[str, Any]

class PilotStopRequest(BaseModel):
    pilot_id: str
