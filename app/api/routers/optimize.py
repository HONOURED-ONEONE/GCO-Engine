from fastapi import APIRouter, HTTPException
from app.api.models.schemas import OptimizeRecommendRequest, OptimizeRecommendResponse
from app.api.services.optimizer import recommend_setpoints

router = APIRouter()

@router.post("/recommend", response_model=OptimizeRecommendResponse)
async def recommend(request: OptimizeRecommendRequest):
    setpoints, rationale, within_bounds, weights = recommend_setpoints(request.batch_id, request.ts)
    if setpoints is None:
        raise HTTPException(status_code=404, detail=rationale)
    
    return OptimizeRecommendResponse(
        setpoints=setpoints,
        rationale=rationale,
        within_bounds=within_bounds,
        objective_weights=weights
    )
