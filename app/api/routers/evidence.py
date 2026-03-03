from fastapi import APIRouter, Depends
from app.api.models.schemas import EvidenceSnapshotResponse, RunMetricsResponse
from app.api.services.corridor import get_active_corridor, get_all_proposals
from app.api.services.kpi import get_recent_kpis
from app.api.utils.audit import get_audit_entries
from app.api.utils.metrics import metrics
from app.api.utils.security import check_role
import uuid

router = APIRouter()
RUN_ID = str(uuid.uuid4())[:8]

@router.get("/snapshot", response_model=EvidenceSnapshotResponse)
async def get_evidence_snapshot(user: dict = Depends(check_role(["Admin", "Engineer", "Auditor"]))):
    active_v, active_data = get_active_corridor()
    return EvidenceSnapshotResponse(
        active_version=active_v,
        bounds=active_data["bounds"],
        recent_kpis=get_recent_kpis(20),
        recent_recommendations=[], # stashed if we had a rec store, for MVP we skip
        proposals=get_all_proposals(),
        audit_tail=get_audit_entries(50)
    )

@router.get("/metrics", response_model=RunMetricsResponse)
async def get_run_metrics(user: dict = Depends(check_role(["Admin", "Engineer", "Auditor"]))):
    props = get_all_proposals()
    return RunMetricsResponse(
        run_id=RUN_ID,
        uptime_sec=metrics.get_uptime_sec(),
        calls_total=metrics.calls_total,
        latency_ms_p95=metrics.get_p95_ms(),
        solver_success_rate=metrics.get_custom("solver_success", 0) / max(1, metrics.calls_total),
        proposal_count=len(props),
        approval_count=len([p for p in props if p["status"] == "approved"])
    )
