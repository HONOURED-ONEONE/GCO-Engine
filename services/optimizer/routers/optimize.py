from fastapi import APIRouter, HTTPException, Query, Depends, Request
from services.optimizer.models.schemas import (
    OptimizeRecommendRequest, OptimizeRecommendResponse, 
    OptimizePreviewResponse, OptimizeHealthResponse, CacheStats
)
from services.optimizer.services.nmpc import recommend_setpoints, get_preview
from services.optimizer.clients.governance_client import governance_client
from services.optimizer.utils.metrics import metrics
from services.optimizer.utils.security import check_role

router = APIRouter()

def get_active_context(request: Request):
    auth_header = request.headers.get("Authorization")
    try:
        active_state = governance_client.get_active_state(auth_header)
        bounds = active_state.get("bounds", {})
        weights = active_state.get("weights", {})
        return bounds, weights
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@router.post("/recommend", response_model=OptimizeRecommendResponse)
async def recommend(req: OptimizeRecommendRequest, request: Request, user: dict = Depends(check_role(["Operator", "Engineer", "Admin"]))):
    bounds, weights = get_active_context(request)
    res, err = recommend_setpoints(req.batch_id, req.ts, req.hints, bounds=bounds, weights=weights)
    if res is None:
        raise HTTPException(status_code=404, detail=err)
    
    ot_status = {"write_attempted": False}
    # No OT writing done here, it's just NMPC optimization in stage-1
    res["ot_status"] = ot_status
    return OptimizeRecommendResponse(**res)

@router.get("/preview", response_model=OptimizePreviewResponse)
async def preview(
    request: Request,
    batch_id: str, 
    window: int = Query(20, ge=1, le=100), 
    step_sec: int = Query(5, ge=1, le=60),
    user: dict = Depends(check_role(["Operator", "Engineer", "Admin"]))
):
    bounds, weights = get_active_context(request)
    res, err = get_preview(batch_id, window, step_sec, bounds=bounds, weights=weights)
    if res is None:
        raise HTTPException(status_code=404, detail=err)
    
    return OptimizePreviewResponse(**res)

@router.get("/health", response_model=OptimizeHealthResponse)
async def health(user: dict = Depends(check_role(["Operator", "Engineer", "Admin"]))):
    return OptimizeHealthResponse(
        uptime_sec=metrics.get_uptime_sec(),
        calls_total=metrics.calls_total,
        cache=CacheStats(
            bounds_hits=governance_client.hits,
            bounds_misses=governance_client.misses,
            ttl_sec=5
        ),
        latency_ms_p50=metrics.get_p50_ms(),
        latency_ms_p95=metrics.get_p95_ms(),
        solver="CasADi/IPOPT",
        solver_success_rate=metrics.get_custom("solver_success", 0) / max(1, metrics.calls_total)
    )
