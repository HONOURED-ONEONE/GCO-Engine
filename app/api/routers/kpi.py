from typing import Optional
from fastapi import APIRouter, Query, Depends
from app.api.models.schemas import KPIIngestRequest, KPIIngestResponse, KPIRecentResponse
from app.api.services.kpi import ingest_kpi_service, get_recent_kpis
from app.api.utils.security import check_role

router = APIRouter()

@router.post("/ingest", response_model=KPIIngestResponse)
async def ingest_kpi(request: KPIIngestRequest, user: dict = Depends(check_role(["Operator", "Admin"]))):
    anomaly, is_updated, prop_id = ingest_kpi_service(
        request.batch_id, 
        request.energy_kwh, 
        request.yield_pct, 
        request.quality_deviation
    )
    
    message = "ingested" if not is_updated else "updated"
    
    return KPIIngestResponse(
        ok=True,
        anomaly_flag=anomaly,
        message=message,
        marl_proposal_created=prop_id is not None,
        proposal_id=prop_id
    )

@router.get("/recent", response_model=KPIRecentResponse)
async def recent_kpis(limit: int = Query(50, ge=1, le=100), user: dict = Depends(check_role(["Operator", "Engineer", "Admin"]))):
    items = get_recent_kpis(limit)
    return KPIRecentResponse(items=items, count=len(items))
