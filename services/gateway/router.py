from fastapi import APIRouter, Request, Response, HTTPException
import httpx
import uuid
from typing import Optional
import time
import asyncio
from .config import GOVERNANCE_BASE, OPTIMIZER_BASE, MONOLITH_BASE, LLM_BASE, KPI_BASE, POLICY_BASE, GATEWAY_SYSTEM_TOKEN
from .security import extract_claims
from .opa_client import evaluate

router = APIRouter()

# Client used for forwarding requests
client = httpx.AsyncClient(timeout=httpx.Timeout(connect=2.0, read=30.0))

@router.get("/")
async def root():
    return {"message": "gateway running"}

@router.get("/gateway/status")
async def status():
    statuses = {}
    for name, base in [("governance", GOVERNANCE_BASE), ("optimizer", OPTIMIZER_BASE), ("monolith", MONOLITH_BASE), ("llm", LLM_BASE), ("kpi", KPI_BASE), ("policy", POLICY_BASE)]:
        try:
            r = await client.get(f"{base}/")
            statuses[name] = "up" if r.status_code == 200 else "error"
        except:
            statuses[name] = "down"
    return statuses

async def emit_audit(event_data: dict):
    try:
        await client.post(
            f"{GOVERNANCE_BASE}/governance/audit/ingest",
            json=event_data,
            headers={"Authorization": f"Bearer {GATEWAY_SYSTEM_TOKEN}"}
        )
    except Exception:
        pass

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(path: str, request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
        
    token = auth_header.split(" ")[1]
    claims = extract_claims(token)
    
    req_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
    full_path = f"/{path}"

    if full_path.startswith("/corridor/") or full_path.startswith("/mode/") or full_path.startswith("/governance/"):
        upstream_base = GOVERNANCE_BASE
        service_name = "governance"
    elif full_path.startswith("/optimize/"):
        upstream_base = OPTIMIZER_BASE
        service_name = "optimizer"
    elif full_path.startswith("/llm/"):
        upstream_base = LLM_BASE
        service_name = "llm"
    elif full_path.startswith("/kpi/"):
        upstream_base = KPI_BASE
        service_name = "kpi"
    elif full_path.startswith("/policy/"):
        upstream_base = POLICY_BASE
        service_name = "policy"
    else:
        upstream_base = MONOLITH_BASE
        service_name = "monolith"

    opa_input = {
        "request": {
            "method": request.method,
            "path": full_path,
            "query": dict(request.query_params),
            "headers": dict(request.headers),
            "claims": claims,
            "x_request_id": req_id
        },
        "resource": {
            "service": service_name
        },
        "context": {
            "ip": request.client.host if request.client else "",
            "ts": str(time.time())
        }
    }

    allow, pdp_headers = await evaluate(client, opa_input)
    
    asyncio.create_task(emit_audit({
        "type": "gateway_decision",
        "data": {
            "route": full_path,
            "subject": claims.get("sub"),
            "allow": allow,
            "x_request_id": req_id,
            "policy_version": pdp_headers.get("X-Policy-Version", "unknown")
        }
    }))

    if not allow:
        raise HTTPException(status_code=403, detail="Forbidden by policy")

    url = f"{upstream_base}{full_path}"
    if request.url.query:
        url += f"?{request.url.query}"
        
    fwd_headers = {
        "Authorization": auth_header,
        "X-Request-Id": req_id,
    }
    if "content-type" in request.headers:
        fwd_headers["content-type"] = request.headers["content-type"]
    
    fwd_headers.update(pdp_headers)
    
    body = await request.body()
    
    try:
        response = await client.request(
            method=request.method,
            url=url,
            headers=fwd_headers,
            content=body
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Bad Gateway: {str(e)}")

    excluded_headers = {"content-length", "content-encoding", "transfer-encoding"}
    res_headers = {k: v for k, v in response.headers.items() if k.lower() not in excluded_headers}

    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=res_headers
    )
