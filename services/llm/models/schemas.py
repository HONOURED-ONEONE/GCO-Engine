from pydantic import BaseModel, ConfigDict
from typing import Dict, List, Any, Optional

class EvidenceMetrics(BaseModel):
    model_config = ConfigDict(extra='allow')
    energy_delta_pct: float
    quality_issues: int
    yield_mean: float

class Counterfactual(BaseModel):
    model_config = ConfigDict(extra='allow')
    expected_energy_delta_pct: float
    risk_quality: str

class Evidence(BaseModel):
    model_config = ConfigDict(extra='allow')
    summary: str
    metrics: EvidenceMetrics
    kpi_window: List[str]
    counterfactuals: Dict[str, Counterfactual]

class Proposal(BaseModel):
    model_config = ConfigDict(extra='allow')
    id: str
    delta: Dict[str, float]
    evidence: Evidence
    context: Dict[str, Any]

class Ask(BaseModel):
    audience: str
    tone: str
    sections: List[str]

class ExplainRequest(BaseModel):
    proposal: Proposal
    ask: Ask

class Narrative(BaseModel):
    rationale: str
    risks: List[str]
    assumptions: List[str]
    operator_checklist: Optional[List[str]] = None

class ValidationRules(BaseModel):
    tolerances: Dict[str, float]
    forbidden_phrases: List[str]

class ValidateRequest(BaseModel):
    proposal: Proposal
    narrative: Narrative
    rules: ValidationRules

class Bounds(BaseModel):
    lower: float
    upper: float

class SnapshotActiveVersion(BaseModel):
    model_config = ConfigDict(extra='allow')
    temperature: Bounds
    flow: Bounds

class Kpi(BaseModel):
    model_config = ConfigDict(extra='allow')
    batch_id: str
    energy_kwh: float
    yield_pct: float
    quality_deviation: bool

class SnapshotProposal(BaseModel):
    model_config = ConfigDict(extra='allow')
    id: str
    delta: Dict[str, float]
    status: str

class Snapshot(BaseModel):
    model_config = ConfigDict(extra='allow')
    active_version: str
    bounds: Dict[str, Bounds]
    recent_kpis: List[Kpi]
    proposals: List[SnapshotProposal]
    system_metrics: Dict[str, Any]

class SummaryRequest(BaseModel):
    snapshot: Snapshot
    style: str
    length: str

class Explanation(BaseModel):
    rationale: str
    risks: List[str]
    assumptions: List[str]
    operator_checklist: List[str]

class Trace(BaseModel):
    numbers_used: List[str]
    omitted_numbers: List[str]
    policy_version: str

class SafetyReport(BaseModel):
    data_usage_ok: bool
    hallucination_risk: str
    overclaim_items: List[Dict[str, Any]]

class ExplainResponse(BaseModel):
    proposal_id: str
    explanation: Explanation
    trace: Trace
    safety_report: SafetyReport

class ValidationIssue(BaseModel):
    type: str
    field: str
    claimed: float
    actual: Optional[float] = None
    tolerance: Optional[float] = None

class ValidationStatus(BaseModel):
    status: str
    issues: List[ValidationIssue]
    forbidden: List[str]

class ValidateResponse(BaseModel):
    proposal_id: str
    validation: ValidationStatus
    safety_report: SafetyReport

class SummarySections(BaseModel):
    overview: str
    kpi_highlights: str
    risks: str
    next_steps: str

class SummaryData(BaseModel):
    title: str
    bullets: List[str]
    sections: SummarySections

class SummaryResponse(BaseModel):
    summary: SummaryData
    safety_report: SafetyReport

class HealthResponse(BaseModel):
    uptime_sec: float
    provider: str
    model_id: str
    calls_total: int
    p95_ms: float
