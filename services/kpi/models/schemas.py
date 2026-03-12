from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any, List

class KPIIngestRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    batch_id: str = Field(..., description="Unique batch identifier")
    energy_kwh: float = Field(..., description="Energy consumption in kWh")
    yield_pct: float = Field(..., description="Yield percentage")
    quality_deviation: bool = Field(..., description="True if there was a quality deviation")
    ts_end: Optional[str] = Field(None, description="ISO-8601 end timestamp")
    meta: Optional[Dict[str, Any]] = Field(None, description="Arbitrary metadata")

class KPIItem(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    batch_id: str
    energy_kwh: float
    yield_pct: float
    quality_deviation: bool
    ingested_at: str
    updated_at: Optional[str] = None
    anomaly_flag: bool
    hash: str
    anomaly_reasons: Optional[List[str]] = None
    ts_end: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

class KPIStatsItem(BaseModel):
    total: int
    last10_p10_p90: Dict[str, List[float]]

class KPIIngestResponse(BaseModel):
    ok: bool
    message: str
    anomaly_flag: bool
    batch_id: str
    stats: KPIStatsItem

class KPIRecentResponse(BaseModel):
    items: List[KPIItem]
    count: int

class KPIStatsResponse(BaseModel):
    p10_p90: Dict[str, List[float]]
    anomaly_count: int

class KPIHealthResponse(BaseModel):
    uptime_sec: float
    calls_total: int
    p50_ms: float
    p95_ms: float
    store_size: int
    failures_total: int
