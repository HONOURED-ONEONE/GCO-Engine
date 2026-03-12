import uuid
from fastapi import APIRouter, HTTPException, Depends
from ..models.schemas import (
    TwinStartRequest, TwinStartResponse, TwinStatusResponse, 
    TwinRunRequest, TwinRunResponse, CounterfactualRequest, CounterfactualResponse
)
from ..services.scenarios import manager
from ..services.simulator import Simulator
from ..services.counterfactual import CounterfactualEngine
from ..utils.metrics import metrics_tracker
from ..security.rbac import require_role, ENGINEER_ADMIN

router = APIRouter()

# Simple in-memory storage for active twin sessions
# For production, use Redis or similar.
active_sessions = {}

@router.post("/start", response_model=TwinStartResponse, dependencies=[Depends(require_role(ENGINEER_ADMIN))])
async def start_twin(req: TwinStartRequest):
    scenario = manager.get_scenario(req.scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    session_id = f"tw-{uuid.uuid4().hex[:8]}"
    active_sessions[session_id] = {
        "scenario_id": req.scenario_id,
        "seed": req.seed,
        "state": scenario.initial_state,
        "progress": 0.0
    }
    metrics_tracker.runs_started += 1
    return TwinStartResponse(session_id=session_id, scenario_id=req.scenario_id, status="running")

@router.get("/status", response_model=TwinStatusResponse)
async def get_status(session_id: str):
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    sess = active_sessions[session_id]
    return TwinStatusResponse(
        session_id=session_id,
        state=sess["state"],
        metrics={"health": 1.0},
        progress=sess["progress"]
    )

@router.post("/run", response_model=TwinRunResponse, dependencies=[Depends(require_role(ENGINEER_ADMIN))])
async def run_twin(req: TwinRunRequest):
    scenario = manager.get_scenario(req.scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    metrics_tracker.runs_started += 1
    timeseries, kpis = Simulator.simulate_run(scenario, req.horizon, req.seed)
    metrics_tracker.total_sim_steps += len(timeseries)
    
    return TwinRunResponse(
        scenario_id=req.scenario_id,
        seed=req.seed,
        timeseries=timeseries,
        kpis=kpis,
        summary={"steps": len(timeseries)}
    )

@router.post("/counterfactual", response_model=CounterfactualResponse, dependencies=[Depends(require_role(ENGINEER_ADMIN))])
async def run_counterfactual(req: CounterfactualRequest):
    try:
        metrics_tracker.counterfactuals_run += 1
        resp = CounterfactualEngine.run_counterfactual(req)
        return resp
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        metrics_tracker.errors += 1
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scenarios")
async def list_scenarios():
    return {"scenarios": manager.list_scenarios()}
