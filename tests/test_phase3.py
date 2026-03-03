import pytest
import os
import json
from fastapi.testclient import TestClient
from app.api.main import app
from app.api.utils.io import KPI_STORE_FILE, REGISTRY_FILE, CORRIDOR_FILE, init_files
from app.api.services.corridor import corridor_cache

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_teardown():
    # Setup: Initialize files
    init_files()
    # Clear caches
    corridor_cache.clear()
    
    # Reset Corridor to baseline
    with open(CORRIDOR_FILE, 'w') as f:
        json.dump({
            "versions": {
                "v1": {
                    "bounds": {
                        "temperature": {"lower": 145.0, "upper": 155.0},
                        "flow": {"lower": 10.0, "upper": 14.0}
                    },
                    "created_at": "2026-02-20T00:00:00Z",
                    "evidence": "Seed bounds based on historical best batches"
                }
            },
            "active_version": "v1"
        }, f)

    # Reset Registry
    with open(REGISTRY_FILE, 'w') as f:
        json.dump({
            "active_version": "v1",
            "history": [{"version": "v1", "at": "2026-03-01T00:00:00Z", "notes": "Initial"}],
            "proposals": [],
            "audit": []
        }, f)
        
    # Clear KPI store
    with open(KPI_STORE_FILE, 'w') as f:
        json.dump({"items": []}, f)
        
    yield

def test_kpi_ingest_idempotent():
    payload = {
        "batch_id": "B99",
        "energy_kwh": 50.0,
        "yield_pct": 95.0,
        "quality_deviation": False
    }
    # First ingest
    resp1 = client.post("/kpi/ingest", json=payload)
    assert resp1.status_code == 200
    assert resp1.json()["message"] == "ingested"
    
    # Second ingest (same batch_id)
    payload["energy_kwh"] = 55.0
    resp2 = client.post("/kpi/ingest", json=payload)
    assert resp2.status_code == 200
    assert resp2.json()["message"] == "updated"
    
    # Verify count is 1
    resp3 = client.get("/kpi/recent")
    assert resp3.json()["count"] == 1
    assert resp3.json()["items"][0]["energy_kwh"] == 55.0

def test_marl_proposal_created_on_energy_improve():
    # Seed 6 KPIs (2 windows of 3)
    # Window 1 (B1-3): avg energy 100
    for i in range(1, 4):
        client.post("/kpi/ingest", json={"batch_id": f"B{i}", "energy_kwh": 100.0, "yield_pct": 90.0, "quality_deviation": False})
    
    # Window 2 (B4-6): avg energy 90 (10% decrease)
    for i in range(4, 7):
        resp = client.post("/kpi/ingest", json={"batch_id": f"B{i}", "energy_kwh": 90.0, "yield_pct": 90.0, "quality_deviation": False})
        if i == 6:
            assert resp.json()["marl_proposal_created"] is True
            assert resp.json()["proposal_id"] is not None

def test_approval_happy_path():
    # Seed 1 proposal manually in registry
    with open(REGISTRY_FILE, 'r') as f:
        registry = json.load(f)
    registry["proposals"].append({
        "id": "prop-test",
        "delta": {"temperature_upper": -0.5},
        "evidence": {"summary": "Test energy improvement", "kpi_window": ["B1","B2"], "metrics": {}, "confidence": 0.8},
        "status": "pending",
        "created_at": "2026-03-03T10:00:00Z"
    })
    with open(REGISTRY_FILE, 'w') as f:
        json.dump(registry, f)
        
    resp = client.post("/corridor/approve", json={
        "proposal_id": "prop-test",
        "decision": "approve",
        "notes": "Looks good"
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"
    assert resp.json()["new_version"] == "v2"
    
    # Verify active version in corridor.json
    with open(CORRIDOR_FILE, 'r') as f:
        corridor = json.load(f)
    assert corridor["active_version"] == "v2"
    assert corridor["versions"]["v2"]["bounds"]["temperature"]["upper"] == 154.5

def test_reject_proposal():
    with open(REGISTRY_FILE, 'r') as f:
        registry = json.load(f)
    registry["proposals"].append({
        "id": "prop-reject",
        "delta": {"temperature_upper": 0.5},
        "evidence": {"summary": "Test reject", "kpi_window": [], "metrics": {}, "confidence": 0.5},
        "status": "pending",
        "created_at": "2026-03-03T10:00:00Z"
    })
    with open(REGISTRY_FILE, 'w') as f:
        json.dump(registry, f)
        
    resp = client.post("/corridor/approve", json={
        "proposal_id": "prop-reject",
        "decision": "reject",
        "notes": "No thanks"
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"
    
    # Verify no version change
    with open(CORRIDOR_FILE, 'r') as f:
        corridor = json.load(f)
    assert corridor["active_version"] == "v1"

def test_delta_limits_and_bounds_invariants():
    # 1. Delta limit clamping
    with open(REGISTRY_FILE, 'r') as f:
        registry = json.load(f)
    registry["proposals"].append({
        "id": "prop-large",
        "delta": {"temperature_upper": -5.0}, # Limit is 1.0
        "evidence": {"summary": "Large delta", "kpi_window": [], "metrics": {}, "confidence": 0.5},
        "status": "pending",
        "created_at": "2026-03-03T10:00:00Z"
    })
    with open(REGISTRY_FILE, 'w') as f:
        json.dump(registry, f)
        
    client.post("/corridor/approve", json={"proposal_id": "prop-large", "decision": "approve"})
    
    with open(CORRIDOR_FILE, 'r') as f:
        corridor = json.load(f)
    assert corridor["versions"]["v2"]["bounds"]["temperature"]["upper"] == 154.0

    # 2. Invariant violation (lower >= upper)
    # Use v2 as base (it is now active)
    with open(CORRIDOR_FILE, 'r') as f:
        corridor = json.load(f)
    active_v = corridor["active_version"] # Should be v2
    corridor["versions"][active_v]["bounds"]["temperature"] = {"lower": 153.5, "upper": 154.0}
    with open(CORRIDOR_FILE, 'w') as f:
        json.dump(corridor, f)
        
    with open(REGISTRY_FILE, 'r') as f:
        registry = json.load(f)
    registry["proposals"].append({
        "id": "prop-bad",
        "delta": {"temperature_upper": -1.0}, # 154 -> 153. Now lower(153.5) > upper(153)
        "evidence": {"summary": "Bad", "kpi_window": [], "metrics": {}, "confidence": 0.5},
        "status": "pending",
        "created_at": "2026-03-03T10:00:00Z"
    })
    with open(REGISTRY_FILE, 'w') as f:
        json.dump(registry, f)
        
    resp = client.post("/corridor/approve", json={"proposal_id": "prop-bad", "decision": "approve"})
    assert resp.json()["status"] == "rejected_due_to_invariants"

def test_diff_endpoint():
    # Start fresh for diff test
    init_files()
    with open(CORRIDOR_FILE, 'r') as f:
        corridor = json.load(f)
    corridor["versions"]["v2"] = {
        "bounds": {
            "temperature": {"lower": 145.0, "upper": 154.0},
            "flow": {"lower": 10.0, "upper": 14.0}
        },
        "created_at": "2026-03-03T11:00:00Z",
        "evidence": "v2 evidence"
    }
    with open(CORRIDOR_FILE, 'w') as f:
        json.dump(corridor, f)
        
    resp = client.get("/corridor/diff", params={"from_v": "v1", "to_v": "v2"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["from_version"] == "v1"
    assert data["to_version"] == "v2"
    assert data["impact_hints"]["energy"] == "likely small decrease"
