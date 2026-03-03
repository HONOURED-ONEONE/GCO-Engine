from fastapi import APIRouter, HTTPException, Query, Depends
from app.api.models.schemas import (
    OptimizeRecommendRequest, OptimizeRecommendResponse, 
    OptimizePreviewResponse, OptimizeHealthResponse, CacheStats
)
from app.api.services.optimizer import recommend_setpoints, get_preview
from app.api.services.corridor import corridor_cache
from app.api.services.ot_connector import ot_connector
from app.api.utils.metrics import metrics
from app.api.utils.security import check_role

router = APIRouter()

@router.post("/recommend", response_model=OptimizeRecommendResponse)
async def recommend(request: OptimizeRecommendRequest, user: dict = Depends(check_role(["Operator", "Engineer", "Admin"]))):
    res, err = recommend_setpoints(request.batch_id, request.ts, request.hints)
    if res is None:
        raise HTTPException(status_code=404, detail=err)
    
    # Phase 4: OT Write-back if requested and armed
    ot_status = {"write_attempted": False}
    if request.write_back:
        success, ot_msg = await ot_connector.write_setpoint(res["setpoints"], request.batch_id)
        ot_status = {
            "write_attempted": True,
            "success": success,
            "message": ot_msg
        }
    
    res["ot_status"] = ot_status
    return OptimizeRecommendResponse(**res)

@router.get("/preview", response_model=OptimizePreviewResponse)
async def preview(
    batch_id: str, 
    window: int = Query(20, ge=1, le=100), 
    step_sec: int = Query(5, ge=1, le=60),
    user: dict = Depends(check_role(["Operator", "Engineer", "Admin"]))
):
    res, err = get_preview(batch_id, window, step_sec)
    if res is None:
        raise HTTPException(status_code=404, detail=err)
    
    return OptimizePreviewResponse(**res)

@router.get("/health", response_model=OptimizeHealthResponse)
async def health(user: dict = Depends(check_role(["Operator", "Engineer", "Admin"]))):
    return OptimizeHealthResponse(
        uptime_sec=metrics.get_uptime_sec(),
        calls_total=metrics.calls_total,
        cache=CacheStats(
            bounds_hits=corridor_cache.hits,
            bounds_misses=corridor_cache.misses,
            ttl_sec=corridor_cache.ttl_sec
        ),
        latency_ms_p50=metrics.get_p50_ms(),
        latency_ms_p95=metrics.get_p95_ms(),
        solver="CasADi/IPOPT",
        solver_success_rate=metrics.get_custom("solver_success", 0) / max(1, metrics.calls_total)
    )
