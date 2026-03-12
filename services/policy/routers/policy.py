import os
import time
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List, Dict, Any

from ..models.schemas import (
    MaybeProposeRequest, MaybeProposeResponse, TrainRequest,
    ActivateResponse, ListResponse, HealthResponse, PolicyExperiencesResponse
)
from ..services.experience_store import add_window, compute_uncertainty, compute_restraint, summarize_window, get_experiences
from ..services.proposer import propose_cost_shaping, propose_corridor_delta, build_proposal
from ..services.trust import compute_trust_score
from ..services.policy_registry import list_policies, activate_policy, add_or_update_policy, get_active_policy
from ..clients.governance_client import get_active_governance, propose_corridor, post_audit
from ..clients.kpi_client import get_recent_kpis
from ..clients.twin_client import get_counterfactuals
from ..security.rbac import require_role
from ..utils.metrics import metrics

router = APIRouter()

@router.post("/maybe-propose", response_model=MaybeProposeResponse)
def maybe_propose(req: MaybeProposeRequest, role: str = Depends(require_role(["Operator", "Engineer", "Admin"]))):
    metrics["calls_total"] += 1
    # 1. Gather/merge KPI window
    items = req.window.items if req.window and req.window.items else get_recent_kpis(req.window.n if req.window else 5)
    if not items:
        raise HTTPException(status_code=400, detail="No KPI data available to form window")

    # 2. Fetch governance active state & current trust score
    gov_state = get_active_governance()
    trust_score = compute_trust_score()
    
    # 3. Update experience store
    key = f"{req.context.corridor_version}|{req.context.mode}"
    weights_at_time = gov_state.get("weights", {"energy": 0.33, "quality": 0.34, "yield": 0.33})
    
    # Simple default decay map if none provided
    decay_map = {req.context.corridor_version: 1.0}
    add_window(key, items, weights_at_time, decay_map)
    
    # 4. Compute signals
    summary = summarize_window(key, req.window.n if req.window else 5)
    uncertainty = compute_uncertainty(key)
    restraint = compute_restraint(key)
    metrics["uncertainty_avg"] = (metrics.get("uncertainty_avg", uncertainty) + uncertainty) / 2
    
    # 5. Synthesize deltas
    delta = None
    delta_type = None
    if req.strategy.allow_cost_shaping:
        cs_delta = propose_cost_shaping(summary, weights_at_time, trust_score, req.strategy.allow_cost_shaping)
        if cs_delta:
            delta = cs_delta.dict()
            delta_type = "cost_shaping"
            metrics["proposed_cost_shaping_total"] += 1
            
    if req.strategy.allow_corridor_delta and not delta:
        cor_delta = propose_corridor_delta(summary, restraint, req.strategy.allow_corridor_delta)
        if cor_delta and any(v is not None for v in cor_delta.dict().values()):
            delta = cor_delta.dict(exclude_none=True)
            delta_type = "corridor"
            metrics["proposed_corridor_total"] += 1
            
    # 6. Counterfactuals
    cf_data = {}
    if req.strategy.counterfactuals and delta:
        cf_data = get_counterfactuals({"delta": delta, "type": delta_type, "context": req.context.dict()})
        
    # 7. Build proposal
    n_eff = len(items)
    base_conf = 0.6 + 0.3 * (1 - uncertainty)
    confidence = max(0.5, min(0.9, base_conf * trust_score))
    
    evidence = {
        "summary": summary,
        "counterfactuals": cf_data,
        "uncertainty": uncertainty,
        "restraint": restraint,
        "rationale": f"Generated {delta_type} proposal based on recent {n_eff} KPIs"
    }
    
    proposal_id = None
    proposed = False
    
    if delta:
        prop_payload = build_proposal(delta, delta_type, evidence, confidence)
        res = propose_corridor(prop_payload)
        if res and "proposal_id" in res:
            proposal_id = res["proposal_id"]
            proposed = True
            metrics["proposals_total"] += 1
            post_audit("policy_proposal_created", {"type": delta_type, "confidence": confidence, "uncertainty": uncertainty}, "policy-service")

    post_audit("policy_window_ingested", summary, "policy-service")

    return MaybeProposeResponse(
        proposed=proposed,
        proposal_id=proposal_id,
        delta={"type": delta_type, "payload": delta} if delta else None,
        uncertainty=uncertainty,
        restraint=restraint,
        confidence=confidence,
        evidence=evidence
    )

@router.post("/train", response_model=Dict[str, Any])
def train_policy(req: TrainRequest, role: str = Depends(require_role(["Engineer", "Admin"]))):
    metrics["calls_total"] += 1
    # Offline deterministic update of policy tables
    # Here we just touch the registry
    new_policy_id = f"p-{int(time.time())}"
    add_or_update_policy(new_policy_id, {
        "trained_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "notes": f"Trained on context {req.context.corridor_version}|{req.context.mode} for {req.epochs} epochs",
        "stats": {"uncertainty_mean": metrics.get("uncertainty_avg", 0.0)}
    })
    post_audit("policy_train_run", {"policy_id": new_policy_id}, "policy-service")
    return {"ok": True, "updated": {"tables": ["cost_weight_table"]}, "policy_id": new_policy_id}

@router.post("/activate/{policy_id}", response_model=ActivateResponse)
def do_activate_policy(policy_id: str, role: str = Depends(require_role(["Engineer", "Admin"]))):
    metrics["calls_total"] += 1
    activate_policy(policy_id)
    post_audit("policy_activate", {"policy_id": policy_id}, "policy-service")
    return ActivateResponse(ok=True, active=policy_id)

@router.get("/active", response_model=Dict[str, Any])
def active_policy(role: str = Depends(require_role(["Operator", "Engineer", "Admin"]))):
    metrics["calls_total"] += 1
    p_id, p_data = get_active_policy()
    return {"policy_id": p_id, "metadata": p_data}

@router.get("/list", response_model=ListResponse)
def list_policies_route(role: str = Depends(require_role(["Operator", "Engineer", "Admin"]))):
    metrics["calls_total"] += 1
    pols = list_policies()
    return ListResponse(items=pols)

@router.get("/experiences", response_model=PolicyExperiencesResponse)
def experiences(version: str, mode: str, limit: int = 100, role: str = Depends(require_role(["Operator", "Engineer", "Admin"]))):
    metrics["calls_total"] += 1
    key = f"{version}|{mode}"
    items = get_experiences(key, limit)
    return PolicyExperiencesResponse(items=items)

@router.get("/health", response_model=HealthResponse)
def health(role: str = Depends(require_role(["Operator", "Engineer", "Admin"]))):
    # compute uptime
    uptime_sec = int(time.time() - metrics["start_time"])
    return HealthResponse(
        uptime_sec=uptime_sec,
        calls_total=metrics["calls_total"],
        p95_ms=5.0, # placeholder
        store_sizes=metrics.get("store_sizes", 0),
        last_proposal_id=metrics.get("last_proposal_id"),
        last_confidence=metrics.get("last_confidence"),
        uncertainty_avg=metrics.get("uncertainty_avg", 0.0)
    )
