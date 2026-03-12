import os
import time
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from typing import Optional

from ..models.schemas import (
    EvidenceSnapshot, EvidenceCaptureRequest, EvidenceCaptureResponse,
    EvidencePackRequest, EvidencePackResponse, EvidenceFilesResponse,
    EvidenceHealthResponse
)
from ..security.rbac import require_roles, get_request_id
from ..services.collect import collector
from ..services.charts import plot_bands, plot_objectives, plot_version_diff
from ..services.report import write_pdf
from ..services.pack import write_sidecars, build_zip
from ..utils.metrics import metrics

router = APIRouter(prefix="/evidence", tags=["evidence"])
EVIDENCE_DIR = os.getenv("EVIDENCE_DIR", "./evidence")

def get_dir_size(path: str) -> str:
    if not os.path.exists(path):
        return "0B"
    total_size = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if total_size < 1024.0:
            return f"{total_size:.1f}{unit}"
        total_size /= 1024.0
    return f"{total_size:.1f}PB"

@router.get("/snapshot", response_model=EvidenceSnapshot, dependencies=[Depends(require_roles(["Operator", "Engineer", "Admin"]))])
async def get_snapshot(
    request: Request,
    include_llm: bool = False,
    include_twin: bool = False,
    rec_limit: int = Query(50),
    x_request_id: Optional[str] = Depends(get_request_id)
):
    start = time.time()
    try:
        snapshot = await collector.gather_snapshot(include_llm, include_twin, rec_limit)
        run_id = snapshot["run_id"]
        
        # Save locally
        collector.save_snapshot(run_id, snapshot)
        
        # Audit
        await collector.post_audit("evidence_snapshot_built", {"run_id": run_id}, "evidence-service", run_id, x_request_id)
        
        metrics.record_call((time.time() - start) * 1000)
        return snapshot
    except Exception as e:
        metrics.record_call((time.time() - start) * 1000)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/capture", response_model=EvidenceCaptureResponse, dependencies=[Depends(require_roles(["Engineer", "Admin"]))])
async def post_capture(
    request: Request,
    payload: EvidenceCaptureRequest,
    x_request_id: Optional[str] = Depends(get_request_id)
):
    start = time.time()
    try:
        run_id = payload.run_id
        if not run_id:
            # Generate new if not provided
            snap = await collector.gather_snapshot(False, False, 50)
            run_id = snap["run_id"]
            collector.save_snapshot(run_id, snap)
            snapshot = snap
        else:
            snapshot = collector.load_snapshot(run_id)
            if not snapshot:
                raise HTTPException(status_code=404, detail="Snapshot not found")
        
        charts_created = []
        for chart in payload.charts:
            chart_path = os.path.join(EVIDENCE_DIR, run_id, "charts", f"{chart}.png")
            if chart == "bands":
                plot_bands(snapshot, chart_path, payload.style)
            elif chart == "objectives":
                plot_objectives(snapshot, chart_path, payload.style)
            elif chart == "version_diff":
                plot_version_diff(snapshot, chart_path, payload.style)
            charts_created.append(f"evidence/{run_id}/charts/{chart}.png")
            
        await collector.post_audit("evidence_charts_rendered", {"charts": payload.charts}, "evidence-service", run_id, x_request_id)
        
        metrics.record_call((time.time() - start) * 1000)
        return EvidenceCaptureResponse(ok=True, run_id=run_id, charts=charts_created)
    except HTTPException as e:
        metrics.record_call((time.time() - start) * 1000)
        raise e
    except Exception as e:
        metrics.record_call((time.time() - start) * 1000)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pack", response_model=EvidencePackResponse, dependencies=[Depends(require_roles(["Engineer", "Admin"]))])
async def post_pack(
    request: Request,
    payload: EvidencePackRequest,
    x_request_id: Optional[str] = Depends(get_request_id)
):
    start = time.time()
    try:
        run_id = payload.run_id
        if not run_id:
            snap = await collector.gather_snapshot(False, False, 50)
            run_id = snap["run_id"]
            collector.save_snapshot(run_id, snap)
            snapshot = snap
        else:
            snapshot = collector.load_snapshot(run_id)
            if not snapshot:
                raise HTTPException(status_code=404, detail="Snapshot not found")
                
        run_dir = os.path.join(EVIDENCE_DIR, run_id)
        
        # Check charts, generate if missing
        chart_paths = []
        for chart in ["bands", "objectives", "version_diff"]:
            p = os.path.join(run_dir, "charts", f"{chart}.png")
            if not os.path.exists(p):
                if chart == "bands": plot_bands(snapshot, p)
                elif chart == "objectives": plot_objectives(snapshot, p)
                elif chart == "version_diff": plot_version_diff(snapshot, p)
            chart_paths.append(p)
            
        # Sidecars
        write_sidecars(run_id, snapshot, EVIDENCE_DIR)
        
        # PDF
        pdf_path = os.path.join(run_dir, "run_report.pdf")
        write_pdf(run_id, payload.title, payload.notes, snapshot, chart_paths, pdf_path)
        
        # Zip
        zip_path = os.path.join(EVIDENCE_DIR, f"gcoengine_evidence_{run_id}.zip")
        build_zip(run_id, run_dir, zip_path)
        
        # Gather all files inside run_dir + zip
        files = []
        for root, _, fs in os.walk(run_dir):
            for f in fs:
                rel = os.path.relpath(os.path.join(root, f), start=EVIDENCE_DIR)
                files.append(f"evidence/{rel}")
        files.append(f"evidence/gcoengine_evidence_{run_id}.zip")
        
        await collector.post_audit("evidence_pack_built", {"pdf": f"evidence/{run_id}/run_report.pdf", "zip": f"evidence/gcoengine_evidence_{run_id}.zip"}, "evidence-service", run_id, x_request_id)
        
        metrics.record_call((time.time() - start) * 1000)
        return EvidencePackResponse(
            ok=True,
            run_id=run_id,
            pdf=f"evidence/{run_id}/run_report.pdf",
            zip=f"evidence/gcoengine_evidence_{run_id}.zip",
            files=files
        )
    except HTTPException as e:
        metrics.record_call((time.time() - start) * 1000)
        raise e
    except Exception as e:
        metrics.record_call((time.time() - start) * 1000)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files", response_model=EvidenceFilesResponse, dependencies=[Depends(require_roles(["Operator", "Engineer", "Admin"]))])
async def get_files(run_id: str = Query(...)):
    start = time.time()
    try:
        run_dir = os.path.join(EVIDENCE_DIR, run_id)
        if not os.path.exists(run_dir):
            raise HTTPException(status_code=404, detail="Run not found")
            
        files = []
        for root, _, fs in os.walk(run_dir):
            for f in fs:
                rel = os.path.relpath(os.path.join(root, f), start=EVIDENCE_DIR)
                files.append(f"evidence/{rel}")
                
        metrics.record_call((time.time() - start) * 1000)
        return EvidenceFilesResponse(files=files)
    except HTTPException as e:
        metrics.record_call((time.time() - start) * 1000)
        raise e
    except Exception as e:
        metrics.record_call((time.time() - start) * 1000)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=EvidenceHealthResponse, dependencies=[Depends(require_roles(["Engineer", "Admin"]))])
async def get_health():
    return EvidenceHealthResponse(
        uptime_sec=metrics.get_uptime(),
        calls_total=metrics.calls_total,
        p50_ms=metrics.get_p50(),
        p95_ms=metrics.get_p95(),
        audit_failures=metrics.audit_failures,
        downstream_failures=metrics.downstream_failures,
        evidence_dir_size=get_dir_size(EVIDENCE_DIR)
    )
