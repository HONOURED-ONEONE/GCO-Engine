from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any

class EvidenceSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")
    active_version: str
    bounds: Dict[str, Any]
    mode: str
    weights: Dict[str, Any]
    proposals: List[Dict[str, Any]]
    recent_kpis: List[Dict[str, Any]]
    recent_recommendations: Optional[List[Dict[str, Any]]] = None
    policy: Optional[Dict[str, Any]] = None
    optimizer_health: Dict[str, Any]
    twin: Optional[Dict[str, Any]] = None
    llm: Optional[Dict[str, Any]] = None
    collected_at: str
    run_id: str

class EvidenceCaptureRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run_id: Optional[str] = None
    charts: List[str] = ["bands", "objectives", "version_diff"]
    style: str = "light"

class EvidenceCaptureResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ok: bool
    run_id: str
    charts: List[str]

class EvidencePackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run_id: Optional[str] = None
    title: str = "Golden Corridor Evidence"
    notes: Optional[str] = None

class EvidencePackResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ok: bool
    run_id: str
    pdf: str
    zip: str
    files: List[str]

class EvidenceFilesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    files: List[str]

class EvidenceHealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    uptime_sec: float
    calls_total: int
    p50_ms: float
    p95_ms: float
    audit_failures: int
    downstream_failures: int
    evidence_dir_size: str
