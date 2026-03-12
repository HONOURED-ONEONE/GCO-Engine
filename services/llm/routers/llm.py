import json
import time
from fastapi import APIRouter, Depends, Request, HTTPException
from ..models.schemas import (
    ExplainRequest, ExplainResponse, Explanation, Trace, SafetyReport,
    ValidateRequest, ValidateResponse, ValidationStatus, ValidationIssue,
    SummaryRequest, SummaryResponse, SummaryData, SummarySections, HealthResponse
)
from ..security.rbac import require_role
from ..clients.llm_client import llm_client, PROVIDER, MODEL_ID
from ..clients.governance_client import governance_client
from ..services.prompt_templates import (
    SYSTEM_EXPLAIN, SYSTEM_VALIDATE, SYSTEM_SUMMARY,
    build_explain_prompt, build_validate_prompt, build_summary_prompt
)
from ..services.claim_checker import check_numbers_in_text, check_forbidden_phrases, build_safety_report, extract_numbers
from ..utils.metrics import metrics

import asyncio
from typing import Dict, Any

router = APIRouter()

uptime_start = time.time()

def _gather_metrics(evidence) -> Dict[str, float]:
    m = {}
    if hasattr(evidence, 'metrics') and evidence.metrics:
        m.update(evidence.metrics.model_dump())
    if hasattr(evidence, 'counterfactuals') and evidence.counterfactuals:
        for k, cf in evidence.counterfactuals.items():
            if isinstance(cf, dict):
                m.update({f"{k}_{k2}": v for k2, v in cf.items() if isinstance(v, (int, float))})
            elif hasattr(cf, 'model_dump'):
                m.update({f"{k}_{k2}": v for k2, v in cf.model_dump().items() if isinstance(v, (int, float))})
    return m

@router.post("/proposal/explain", response_model=ExplainResponse, response_model_exclude_none=True)
async def explain_proposal(req: ExplainRequest, request: Request):
    claims = require_role(request, ["Engineer", "Admin"])
    start = time.time()
    
    try:
        user_prompt = build_explain_prompt(req.proposal.model_dump_json(), req.ask.model_dump_json())
        res = await llm_client.complete(SYSTEM_EXPLAIN, user_prompt, {"properties": {"rationale": {"type": "string"}}})
        
        try:
            parsed = json.loads(res["text"])
        except json.JSONDecodeError:
            parsed = {"rationale": "Failed to parse explanation", "risks": [], "assumptions": [], "operator_checklist": []}
            
        text_content = json.dumps(parsed)
        ev_metrics = _gather_metrics(req.proposal.evidence)
        issues = check_numbers_in_text(text_content, ev_metrics, {})
        safety = build_safety_report(issues, [])
        
        explanation = Explanation(
            rationale=parsed.get("rationale", ""),
            risks=parsed.get("risks", []),
            assumptions=parsed.get("assumptions", []),
            operator_checklist=parsed.get("operator_checklist", [])
        )
        
        trace = Trace(
            numbers_used=[f"{num}" for num in extract_numbers(text_content)],
            omitted_numbers=[],
            policy_version="v1-stage2"
        )
        
        safety_report = SafetyReport(**safety)
        
        response_data = ExplainResponse(
            proposal_id=req.proposal.id,
            explanation=explanation,
            trace=trace,
            safety_report=safety_report
        )
        
        asyncio.create_task(governance_client.post_audit(
            event_type="llm_explain",
            data={"proposal_id": req.proposal.id, "safety_risk": safety_report.hallucination_risk},
            subject=claims.get("sub", "llm-service")
        ))
        
        metrics.record_call()
        metrics.record_latency((time.time() - start) * 1000)
        
        return response_data

    except Exception as e:
        metrics.record_provider_failure()
        raise HTTPException(status_code=502, detail="LLM Provider Error")

@router.post("/proposal/validate", response_model=ValidateResponse, response_model_exclude_none=True)
async def validate_proposal(req: ValidateRequest, request: Request):
    claims = require_role(request, ["Engineer", "Admin"])
    start = time.time()
    
    try:
        user_prompt = build_validate_prompt(
            req.proposal.model_dump_json(),
            req.narrative.model_dump_json(),
            req.rules.model_dump_json()
        )
        
        res = await llm_client.complete(SYSTEM_VALIDATE, user_prompt, {"properties": {"status": {"type": "string"}}})
        
        try:
            parsed = json.loads(res["text"])
        except json.JSONDecodeError:
            parsed = {"status": "fail", "issues": [], "forbidden": []}
            
        ev_metrics = _gather_metrics(req.proposal.evidence)
        narrative_text = req.narrative.model_dump_json()
        
        issues_dict = check_numbers_in_text(narrative_text, ev_metrics, req.rules.tolerances)
        forbidden = check_forbidden_phrases(narrative_text, req.rules.forbidden_phrases)
        
        safety = build_safety_report(issues_dict, forbidden)
        
        # Override with our deterministic check if LLM missed it
        issues = [ValidationIssue(**i) for i in issues_dict]
        
        status_val = "pass"
        if safety["hallucination_risk"] == "medium":
            status_val = "warn"
        elif safety["hallucination_risk"] == "high":
            status_val = "fail"
            
        # Merge LLM findings with deterministic findings
        if parsed.get("status") in ["warn", "fail"]:
            status_val = parsed["status"]
            for i in parsed.get("issues", []):
                issues.append(ValidationIssue(**i))
            for f in parsed.get("forbidden", []):
                if f not in forbidden:
                    forbidden.append(f)
                    
        validation = ValidationStatus(
            status=status_val,
            issues=issues,
            forbidden=forbidden
        )
        
        safety_report = SafetyReport(**safety)
        
        response_data = ValidateResponse(
            proposal_id=req.proposal.id,
            validation=validation,
            safety_report=safety_report
        )
        
        asyncio.create_task(governance_client.post_audit(
            event_type="llm_validate",
            data={"proposal_id": req.proposal.id, "status": status_val},
            subject=claims.get("sub", "llm-service")
        ))
        
        metrics.record_call()
        metrics.record_latency((time.time() - start) * 1000)
        
        return response_data

    except Exception as e:
        metrics.record_provider_failure()
        raise HTTPException(status_code=502, detail="LLM Provider Error")

@router.post("/evidence/summary", response_model=SummaryResponse, response_model_exclude_none=True)
async def summarize_evidence(req: SummaryRequest, request: Request):
    claims = require_role(request, ["Operator", "Engineer", "Admin"])
    start = time.time()
    
    try:
        user_prompt = build_summary_prompt(req.snapshot.model_dump_json(), req.style, req.length)
        res = await llm_client.complete(SYSTEM_SUMMARY, user_prompt, {"properties": {"sections": {"type": "object"}}})
        
        try:
            parsed = json.loads(res["text"])
        except json.JSONDecodeError:
            parsed = {"title": "Summary", "bullets": [], "sections": {}}
            
        sections = parsed.get("sections", {})
        summary = SummaryData(
            title=parsed.get("title", "Snapshot Summary"),
            bullets=parsed.get("bullets", []),
            sections=SummarySections(
                overview=sections.get("overview", ""),
                kpi_highlights=sections.get("kpi_highlights", ""),
                risks=sections.get("risks", ""),
                next_steps=sections.get("next_steps", "")
            )
        )
        
        # A simple safety report
        safety_report = SafetyReport(
            data_usage_ok=True,
            hallucination_risk="low",
            overclaim_items=[]
        )
        
        response_data = SummaryResponse(
            summary=summary,
            safety_report=safety_report
        )
        
        asyncio.create_task(governance_client.post_audit(
            event_type="llm_evidence_summary",
            data={"active_version": req.snapshot.active_version},
            subject=claims.get("sub", "llm-service")
        ))
        
        metrics.record_call()
        metrics.record_latency((time.time() - start) * 1000)
        
        return response_data

    except Exception as e:
        metrics.record_provider_failure()
        raise HTTPException(status_code=502, detail="LLM Provider Error")

@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        uptime_sec=time.time() - uptime_start,
        provider=PROVIDER,
        model_id=MODEL_ID,
        calls_total=metrics.calls_total,
        p95_ms=metrics.get_p95_ms()
    )
