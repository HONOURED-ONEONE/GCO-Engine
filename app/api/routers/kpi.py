from fastapi import APIRouter
from app.api.models.schemas import KPIIngestRequest, KPIIngestResponse
from app.api.utils.io import read_json, write_json, KPI_STORE_FILE
from app.api.services.marl import maybe_propose_update

router = APIRouter()

@router.post("/ingest", response_model=KPIIngestResponse)
async def ingest_kpi(request: KPIIngestRequest):
    store = read_json(KPI_STORE_FILE)
    if "items" not in store:
        store["items"] = []
    
    store["items"].append(request.dict())
    write_json(KPI_STORE_FILE, store)
    
    # Anomaly Rule: yield < 80 or quality issues
    anomaly = request.quality_deviation or request.yield_pct < 80.0
    
    # Mock MARL check
    prop_id = maybe_propose_update()
    
    message = "KPI ingested successfully."
    if prop_id:
        message += f" New corridor proposal triggered: {prop_id}"
    
    return KPIIngestResponse(
        ok=True,
        anomaly_flag=anomaly,
        message=message
    )
