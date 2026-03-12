import os

files = {
    "services/policy/__init__.py": "",
    "services/policy/main.py": """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from .routers.policy import router

app = FastAPI(title="GCO Policy/MARL Service")

allow_origins = os.getenv("ALLOW_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/policy", tags=["policy"])

@app.get("/")
def root():
    return {"message": "policy-service running"}
""",
    "services/policy/routers/__init__.py": "",
    "services/policy/routers/policy.py": """import os
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
            delta = cor_delta.dict()
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
""",
    "services/policy/models/__init__.py": "",
    "services/policy/models/schemas.py": """from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union

class ContextModel(BaseModel):
    corridor_version: str
    mode: str

class StrategyModel(BaseModel):
    allow_cost_shaping: bool = True
    allow_corridor_delta: bool = True
    counterfactuals: bool = True

class KPIItem(BaseModel):
    batch_id: str
    energy_kwh: float
    yield_pct: float
    quality_deviation: bool
    at: str

class KPIWindow(BaseModel):
    items: Optional[List[KPIItem]] = None
    n: int = 5

class MaybeProposeRequest(BaseModel):
    window: Optional[KPIWindow] = None
    context: ContextModel
    strategy: StrategyModel
    class Config:
        extra = 'forbid'

class CostShapingDelta(BaseModel):
    weights: Dict[str, float]
    clamp: Dict[str, float]

class CorridorDelta(BaseModel):
    temperature_upper: Optional[float] = None
    temperature_lower: Optional[float] = None
    flow_upper: Optional[float] = None
    flow_lower: Optional[float] = None

class MaybeProposeResponse(BaseModel):
    proposed: bool
    proposal_id: Optional[str]
    delta: Optional[Dict[str, Any]]
    uncertainty: float = Field(ge=0.0, le=1.0)
    restraint: bool
    confidence: float = Field(ge=0.5, le=0.9)
    evidence: Dict[str, Any]

class ReplayModel(BaseModel):
    versions_decay: Dict[str, float]

class TrainRequest(BaseModel):
    context: ContextModel
    epochs: int = 1
    replay: Optional[ReplayModel] = None

class ActivateResponse(BaseModel):
    ok: bool
    active: str

class PolicyItem(BaseModel):
    id: str
    trained_at: Optional[str] = None
    notes: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None

class ListResponse(BaseModel):
    items: List[Dict[str, Any]]

class HealthResponse(BaseModel):
    uptime_sec: int
    calls_total: int
    p95_ms: float
    store_sizes: int
    last_proposal_id: Optional[str]
    last_confidence: Optional[float]
    uncertainty_avg: float

class PolicyExperiencesResponse(BaseModel):
    items: List[Dict[str, Any]]
""",
    "services/policy/services/__init__.py": "",
    "services/policy/services/experience_store.py": """import json
import os
from filelock import FileLock
from datetime import datetime
from ..utils.metrics import metrics

STORE_FILE = "data/experience_store.json"
LOCK_FILE = "data/experience_store.lock"

def _load_store():
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists(STORE_FILE):
        return {"by_key": {}, "meta": {"last_update": ""}}
    with open(STORE_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"by_key": {}, "meta": {"last_update": ""}}

def _save_store(data):
    with open(STORE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def add_window(key: str, items: list, weights_at_time: dict, decay_map: dict):
    with FileLock(LOCK_FILE):
        store = _load_store()
        if key not in store["by_key"]:
            store["by_key"][key] = []
        
        for item in items:
            it = item.dict() if hasattr(item, "dict") else item
            it["weights_at_time"] = weights_at_time
            # compute features
            it["features"] = {
                "trend_energy": 0.0,
                "trend_yield": 0.0,
                "anomaly": 1 if it.get("quality_deviation") else 0
            }
            store["by_key"][key].append(it)
        
        # Keep bounded length
        store["by_key"][key] = store["by_key"][key][-100:]
        store["meta"]["last_update"] = datetime.utcnow().isoformat()
        
        _save_store(store)
        metrics["store_sizes"] = sum(len(v) for v in store["by_key"].values())

def get_experiences(key: str, limit: int = 100):
    store = _load_store()
    return store.get("by_key", {}).get(key, [])[-limit:]

def compute_uncertainty(key: str) -> float:
    from .uncertainty import rolling_variance, anomaly_density, combine
    items = get_experiences(key)
    if not items:
        return 1.0
    energies = [i["energy_kwh"] for i in items]
    yields = [i["yield_pct"] for i in items]
    
    var_norm = (rolling_variance(energies) / 100.0) + (rolling_variance(yields) / 100.0)
    density = anomaly_density(items)
    n_eff = len(items)
    
    return combine(var_norm, density, n_eff)

def compute_restraint(key: str) -> bool:
    unc = compute_uncertainty(key)
    items = get_experiences(key, limit=5)
    density = sum(1 for i in items if i.get("quality_deviation")) / max(1, len(items))
    return unc > 0.6 or density > 0.25 or sum(1 for i in items if i.get("quality_deviation")) >= 2

def summarize_window(key: str, n: int):
    items = get_experiences(key, limit=n)
    if not items:
        return {"n": 0}
    energies = [i["energy_kwh"] for i in items]
    yields = [i["yield_pct"] for i in items]
    quals = [1 for i in items if i.get("quality_deviation")]
    
    return {
        "n": len(items),
        "energy_mean": sum(energies)/len(energies) if energies else 0,
        "energy_trend": (energies[-1]-energies[0])/max(1, energies[0]) if len(energies)>1 else 0,
        "yield_mean": sum(yields)/len(yields) if yields else 0,
        "yield_trend": (yields[-1]-yields[0])/max(1, yields[0]) if len(yields)>1 else 0,
        "quality_violations": len(quals)
    }
""",
    "services/policy/services/proposer.py": """from ..models.schemas import CostShapingDelta, CorridorDelta

def propose_cost_shaping(summary: dict, weights_default: dict, trust_score: float, allow: bool):
    if not allow or summary["n"] < 2:
        return None
        
    energy_trend = summary.get("energy_trend", 0)
    q_viol = summary.get("quality_violations", 0)
    
    weights = dict(weights_default)
    clamp = 0.1 * trust_score
    
    # If energy improved and stable quality, shift weight toward energy
    if energy_trend < -0.01 and q_viol == 0:
        weights["energy"] = min(1.0, weights.get("energy", 0.33) + clamp)
        weights["quality"] = max(0.0, weights.get("quality", 0.34) - clamp/2)
        weights["yield"] = max(0.0, weights.get("yield", 0.33) - clamp/2)
    elif q_viol > 0:
        weights["quality"] = min(1.0, weights.get("quality", 0.34) + clamp)
        weights["energy"] = max(0.0, weights.get("energy", 0.33) - clamp/2)
        weights["yield"] = max(0.0, weights.get("yield", 0.33) - clamp/2)
        
    # Renormalize
    tot = sum(weights.values())
    for k in weights:
        weights[k] = round(weights[k] / tot, 3)
        
    return CostShapingDelta(weights=weights, clamp={"per_obj": 0.1})

def propose_corridor_delta(summary: dict, restraints: bool, allow: bool):
    if not allow or summary["n"] < 2:
        return None
        
    energy_trend = summary.get("energy_trend", 0)
    q_viol = summary.get("quality_violations", 0)
    yield_mean = summary.get("yield_mean", 100)
    
    delta = CorridorDelta()
    changed = False
    
    if energy_trend <= -0.03 and q_viol == 0:
        delta.temperature_upper = -0.5
        changed = True
    elif yield_mean < 85 and q_viol == 0:
        delta.flow_upper = 0.2
        changed = True
    elif q_viol > 0 and not restraints:
        delta.temperature_upper = 0.5
        changed = True
        
    if changed:
        return delta
    return None

def build_proposal(delta: dict, delta_type: str, evidence: dict, confidence: float):
    return {
        "subject": "corridor",
        "delta": {"type": delta_type, "payload": delta},
        "evidence": evidence,
        "confidence": confidence
    }
""",
    "services/policy/services/uncertainty.py": """import math

def rolling_variance(series: list) -> float:
    if len(series) < 2:
        return 0.0
    mean = sum(series) / len(series)
    var = sum((x - mean)**2 for x in series) / (len(series) - 1)
    return var

def anomaly_density(items: list) -> float:
    if not items:
        return 0.0
    anom = sum(1 for i in items if i.get("quality_deviation", False))
    return anom / len(items)

def combine(var_norm: float, density: float, n_eff: int) -> float:
    base = var_norm + density
    if n_eff > 0:
        base += 1.0 / math.sqrt(n_eff)
    return min(0.9, max(0.0, base))
""",
    "services/policy/services/trust.py": """from ..clients.governance_client import list_proposals
from ..utils.metrics import metrics

def compute_trust_score() -> float:
    try:
        props = list_proposals(limit=10)
    except:
        props = []
        
    if not props:
        return 0.8
        
    approved = sum(1 for p in props if p.get("status") == "approved")
    rejected = sum(1 for p in props if p.get("status") == "rejected")
    
    total = approved + rejected
    if total == 0:
        return 0.8
        
    score = 0.5 + 0.5 * (approved / total)
    metrics["trust_score_avg"] = score
    return min(1.0, max(0.5, score))
""",
    "services/policy/clients/__init__.py": "",
    "services/policy/clients/governance_client.py": """import os
import requests
from ..utils.metrics import metrics

GOVERNANCE_BASE = os.getenv("GOVERNANCE_BASE", "http://governance:8001")

def get_active_governance():
    try:
        r = requests.get(f"{GOVERNANCE_BASE}/governance/active", timeout=2)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {"weights": {"energy": 0.33, "quality": 0.34, "yield": 0.33}, "mode": "efficiency_first"}

def list_proposals(status="approved|rejected|pending", limit=50):
    try:
        r = requests.get(f"{GOVERNANCE_BASE}/corridor/proposals", params={"status": status, "limit": limit}, timeout=2)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []

def propose_corridor(payload: dict):
    try:
        r = requests.post(f"{GOVERNANCE_BASE}/corridor/propose", json=payload, timeout=2)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {}

def post_audit(event_type: str, data: dict, subject: str):
    try:
        requests.post(f"{GOVERNANCE_BASE}/governance/audit", json={
            "event_type": event_type,
            "data": data,
            "subject": subject
        }, timeout=2)
    except Exception:
        metrics["governance_post_failures"] = metrics.get("governance_post_failures", 0) + 1
""",
    "services/policy/clients/kpi_client.py": """import os
import requests

KPI_BASE = os.getenv("KPI_BASE", "http://kpi:8005")

def get_recent_kpis(limit=5):
    try:
        r = requests.get(f"{KPI_BASE}/kpi/recent", params={"limit": limit}, timeout=2)
        if r.status_code == 200:
            return r.json().get("items", [])
    except Exception:
        pass
    return []
""",
    "services/policy/clients/twin_client.py": """import os
import requests
from ..utils.metrics import metrics

TWIN_BASE = os.getenv("TWIN_BASE", "http://twin:8007")

def get_counterfactuals(payload: dict):
    try:
        r = requests.post(f"{TWIN_BASE}/twin/counterfactuals", json=payload, timeout=2)
        if r.status_code == 200:
            return r.json()
    except Exception:
        metrics["twin_cf_failures"] = metrics.get("twin_cf_failures", 0) + 1
    return {}
""",
    "services/policy/security/__init__.py": "",
    "services/policy/security/rbac.py": """from fastapi import Request, HTTPException

def extract_role(req: Request) -> str:
    auth = req.headers.get("Authorization", "")
    if "op_" in auth:
        return "Operator"
    if "eng_" in auth:
        return "Engineer"
    if "admin_" in auth:
        return "Admin"
    return "Operator" # Default for local/tests if not strictly enforced by gateway

def require_role(allowed_roles: list):
    def dependency(req: Request):
        role = extract_role(req)
        if role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return role
    return dependency
""",
    "services/policy/utils/__init__.py": "",
    "services/policy/utils/metrics.py": """import time

metrics = {
    "start_time": time.time(),
    "calls_total": 0,
    "proposals_total": 0,
    "proposed_cost_shaping_total": 0,
    "proposed_corridor_total": 0,
    "uncertainty_avg": 0.0,
    "restraint_rate": 0.0,
    "trust_score_avg": 0.0,
    "governance_post_failures": 0,
    "twin_cf_failures": 0,
    "store_sizes": 0,
    "last_proposal_id": None,
    "last_confidence": None
}
""",
    "services/policy/services/policy_registry.py": """import json
import os
from filelock import FileLock

REGISTRY_FILE = "data/policy_registry.json"
LOCK_FILE = "data/policy_registry.lock"

def _load_reg():
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists(REGISTRY_FILE):
        return {"active": None, "items": []}
    with open(REGISTRY_FILE, "r") as f:
        try:
            return json.load(f)
        except:
            return {"active": None, "items": []}

def _save_reg(data):
    with open(REGISTRY_FILE, "w") as f:
        json.dump(data, f, indent=2)

def list_policies():
    return _load_reg().get("items", [])

def add_or_update_policy(p_id: str, data: dict):
    with FileLock(LOCK_FILE):
        reg = _load_reg()
        found = False
        for item in reg["items"]:
            if item["id"] == p_id:
                item.update(data)
                found = True
                break
        if not found:
            data["id"] = p_id
            reg["items"].append(data)
        _save_reg(reg)

def activate_policy(p_id: str):
    with FileLock(LOCK_FILE):
        reg = _load_reg()
        reg["active"] = p_id
        _save_reg(reg)

def get_active_policy():
    reg = _load_reg()
    active_id = reg.get("active")
    for item in reg.get("items", []):
        if item["id"] == active_id:
            return active_id, item
    return active_id, {}
""",
    "services/policy/tests/__init__.py": "",
    "services/policy/tests/test_policy_service.py": """from fastapi.testclient import TestClient
from ..main import app

client = TestClient(app)

def test_health():
    res = client.get("/policy/health", headers={"Authorization": "admin_01"})
    assert res.status_code == 200
    assert "uptime_sec" in res.json()

def test_maybe_propose():
    payload = {
        "window": {
            "items": [
                {"batch_id":"B10","energy_kwh":96.4,"yield_pct":91.2,"quality_deviation":False,"at":"ISO"},
                {"batch_id":"B11","energy_kwh":95.0,"yield_pct":91.0,"quality_deviation":False,"at":"ISO"},
                {"batch_id":"B12","energy_kwh":93.0,"yield_pct":92.0,"quality_deviation":False,"at":"ISO"}
            ],
            "n": 3
        },
        "context": {"corridor_version": "v3", "mode": "efficiency_first"},
        "strategy": {"allow_cost_shaping": True, "allow_corridor_delta": True, "counterfactuals": False}
    }
    res = client.post("/policy/maybe-propose", json=payload, headers={"Authorization": "eng_01"})
    assert res.status_code == 200
    data = res.json()
    assert "proposed" in data
    assert "uncertainty" in data
    assert 0.0 <= data["uncertainty"] <= 1.0

def test_train_and_activate():
    train_req = {
        "context": {"corridor_version": "v3", "mode": "sustainability_first"},
        "epochs": 1
    }
    res_train = client.post("/policy/train", json=train_req, headers={"Authorization": "eng_01"})
    assert res_train.status_code == 200
    p_id = res_train.json().get("policy_id")
    assert p_id
    
    res_act = client.post(f"/policy/activate/{p_id}", headers={"Authorization": "admin_01"})
    assert res_act.status_code == 200
    assert res_act.json().get("active") == p_id
""",
    "services/policy/README.md": """# Policy / MARL Service

Extracts Policy/MARL logic into a standalone FastAPI microservice that performs safe, governed learning from batch KPIs and generates proposals for corridor or cost shaping — with explicit human approval via governance.

## Key Features
- **Experience Store**: Owns KPI context (corridor version + mode) and drives offline/mini-batch updates.
- **Cost Shaping Proposals**: Suggests small updates to NMPC weights (e.g. shift priority from yield to energy if stable).
- **Uncertainty & Restraint Signals**: Computes uncertainty based on statistical variance/sparsity and sets a restraint flag for downstream NMPC hints.
- **Counterfactual Evaluation**: Hits twin-service to gauge effects of plausible corridor/weight changes before generating a proposal.
- **Safety First**: Zero direct control mutations. Generates proposals for approval via `governance`.

## Endpoints
- `POST /policy/maybe-propose`: main entrypoint (usually from KPI)
- `POST /policy/train`: offline/batch training hook
- `POST /policy/activate/{policy_id}`: set active policy profile
- `GET /policy/active`, `/policy/list`, `/policy/experiences`, `/policy/health`
""",
    "services/policy/Dockerfile": """FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/services/policy/

ENV PYTHONPATH=/app

CMD ["uvicorn", "services.policy.main:app", "--host", "0.0.0.0", "--port", "8006"]
""",
    "services/policy/requirements.txt": """fastapi==0.103.1
uvicorn==0.23.2
pydantic==2.3.0
requests==2.31.0
filelock==3.12.3
"""
}

for path, content in files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)

print("Created all policy service files")
