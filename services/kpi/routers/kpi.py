from fastapi import APIRouter, Depends, Header, Query, HTTPException, Request, BackgroundTasks
from typing import Optional, Any
import logging
import os

from services.kpi.models.schemas import (
    KPIIngestRequest, KPIIngestResponse, KPIStatsItem,
    KPIRecentResponse, KPIHealthResponse, KPIStatsResponse
)
from services.kpi.services.kpi_store import kpi_store
from services.kpi.services.anomaly import compute_rolling_percentiles, is_anomalous
from services.kpi.clients.governance_client import post_audit
from services.kpi.clients.policy_client import maybe_notify
from services.kpi.security.rbac import require_operator, require_engineer, get_current_subject
from services.kpi.utils.metrics import metrics, timer

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/ingest", response_model=KPIIngestResponse)
async def ingest_kpi(
    req: KPIIngestRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    role: str = Depends(require_operator),
    subject: str = Depends(get_current_subject),
    x_request_id: Optional[str] = Header(None)
):
    with timer():
        metrics.calls_total += 1
        
        # Load all to get recent items for anomaly rules
        data = kpi_store.load_all()
        items = data.get("items", [])
        
        # Compute rolling percentiles for energy
        p10, p90 = compute_rolling_percentiles(items, "energy_kwh", n=10)
        
        # Determine anomaly
        item_dict = req.model_dump()
        anomaly_flag, reasons = is_anomalous(item_dict, (p10, p90), {"items": items})
        
        if anomaly_flag:
            metrics.anomalies_total += 1
            
        item_dict["anomaly_flag"] = anomaly_flag
        item_dict["anomaly_reasons"] = reasons
        
        # Idempotent upsert
        status, updated_data = kpi_store.upsert(item_dict)
        metrics.upserts_total += 1
        
        # Background tasks
        background_tasks.add_task(
            _handle_post_ingest,
            item_dict, status, x_request_id, subject
        )

        return KPIIngestResponse(
            ok=True,
            message=status,
            anomaly_flag=anomaly_flag,
            batch_id=req.batch_id,
            stats=KPIStatsItem(
                total=len(updated_data.get("items", [])),
                last10_p10_p90={"energy_kwh": [p10, p90]}
            )
        )

async def _handle_post_ingest(item: dict, status: str, request_id: str, subject: str):
    # Post audit to governance
    audit_data = {
        "batch_id": item["batch_id"],
        "energy_kwh": item["energy_kwh"],
        "yield_pct": item["yield_pct"],
        "quality_deviation": item["quality_deviation"],
        "anomaly_flag": item["anomaly_flag"]
    }
    
    try:
        await post_audit("kpi_ingest", audit_data, subject, request_id or "")
    except Exception:
        metrics.governance_audit_failures += 1
        
    # Maybe notify policy
    if os.getenv("POLICY_NOTIFY_BASE"):
        try:
            stats = kpi_store.stats_last_n(5)
            summary = {
                "recent_batches": 5,
                "anomalies_in_window": stats["anomaly_count"],
                "trigger_batch": item["batch_id"]
            }
            await maybe_notify(summary, {"X-Request-Id": request_id or ""})
        except Exception:
            metrics.policy_notify_failures += 1

@router.get("/recent", response_model=KPIRecentResponse)
def get_recent_kpis(
    limit: int = Query(50, ge=1, le=500),
    role: str = Depends(require_operator)
):
    with timer():
        metrics.calls_total += 1
        items = kpi_store.recent(limit)
        return KPIRecentResponse(items=items, count=len(items))

@router.get("/health", response_model=KPIHealthResponse)
def get_health(role: str = Depends(require_engineer)):
    with timer():
        metrics.calls_total += 1
        p50, p95 = metrics.get_p50_p95()
        data = kpi_store.load_all()
        return KPIHealthResponse(
            uptime_sec=metrics.get_uptime(),
            calls_total=metrics.calls_total,
            p50_ms=p50,
            p95_ms=p95,
            store_size=len(data.get("items", [])),
            failures_total=metrics.governance_audit_failures + metrics.policy_notify_failures
        )

@router.get("/stats", response_model=KPIStatsResponse)
def get_stats(role: str = Depends(require_engineer)):
    with timer():
        metrics.calls_total += 1
        stats = kpi_store.stats_last_n(10)
        return KPIStatsResponse(
            p10_p90=stats["p10_p90"],
            anomaly_count=stats["anomaly_count"]
        )
