from fastapi import APIRouter, HTTPException, Query
from app.api.models.schemas import (
    OptimizeRecommendRequest, OptimizeRecommendResponse, 
    OptimizePreviewResponse, OptimizeHealthResponse, CacheStats
)
from app.api.services.optimizer import recommend_setpoints, get_preview
from app.api.services.corridor import corridor_cache
from app.api.utils.metrics import metrics

router = APIRouter()

@router.post("/recommend", response_model=OptimizeRecommendResponse)
async def recommend(request: OptimizeRecommendRequest):
    res, err = recommend_setpoints(request.batch_id, request.ts, request.hints)
    if res is None:
        raise HTTPException(status_code=404, detail=err)
    
    return OptimizeRecommendResponse(**res)

@router.get("/preview", response_model=OptimizePreviewResponse)
async def preview(
    batch_id: str, 
    window: int = Query(20, ge=1, le=100), 
    step_sec: int = Query(5, ge=1, le=60)
):
    res, err = get_preview(batch_id, window, step_sec)
    if res is None:
        raise HTTPException(status_code=404, detail=err)
    
    return OptimizePreviewResponse(**res)

@router.get("/health", response_model=OptimizeHealthResponse)
async def health():
    return OptimizeHealthResponse(
        uptime_sec=metrics.get_uptime_sec(),
        calls_total=metrics.calls_total,
        cache=CacheStats(
            bounds_hits=corridor_cache.hits,
            bounds_misses=corridor_cache.misses,
            ttl_sec=corridor_cache.ttl_sec
        ),
        latency_ms_p50=metrics.get_p50_ms(),
        latency_ms_p95=metrics.get_p95_ms()
    )
