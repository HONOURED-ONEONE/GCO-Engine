import pytest
import os
import json
from fastapi.testclient import TestClient
from services.governance.main import app
from services.governance.utils.io import init_files, REGISTRY_FILE, CORRIDOR_FILE

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_teardown():
    # Setup: Ensure fresh registry for tests
    if os.path.exists(REGISTRY_FILE):
        os.remove(REGISTRY_FILE)
    if os.path.exists(CORRIDOR_FILE):
        os.remove(CORRIDOR_FILE)
    init_files()
    yield
    # Teardown: Clean up
    if os.path.exists(REGISTRY_FILE):
        os.remove(REGISTRY_FILE)
    if os.path.exists(CORRIDOR_FILE):
        os.remove(CORRIDOR_FILE)

def test_governance_active():
    response = client.get("/governance/active")
    assert response.status_code == 200
    data = response.json()
    assert "active_version" in data
    assert "bounds" in data
    assert "last_mode" in data
    assert "last_mode_weights" in data
    assert "audit_head_hash" in data

def test_governance_audit_ingest():
    # Admin role required for ingest
    response = client.post(
        "/governance/audit/ingest",
        json={
            "event_type": "test_event",
            "data": {"key": "value"},
            "user_id": "test_user"
        },
        headers={"Authorization": "Bearer admin_01"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "recorded"
    assert "hash" in data
    
    # Verify chain
    with open(REGISTRY_FILE, 'r') as f:
        registry = json.load(f)
        assert len(registry.get("audit", [])) > 0
        last_entry = registry["audit"][-1]
        assert last_entry["type"] == "test_event"
        assert last_entry["data"] == {"key": "value"}

def test_governance_audit_verify_tamper():
    # Ingest 2 entries
    client.post(
        "/governance/audit/ingest",
        json={"event_type": "event_1", "data": {}, "user_id": "admin_01"},
        headers={"Authorization": "Bearer admin_01"}
    )
    client.post(
        "/governance/audit/ingest",
        json={"event_type": "event_2", "data": {}, "user_id": "admin_01"},
        headers={"Authorization": "Bearer admin_01"}
    )
    
    # Verify OK initially
    res = client.get("/governance/audit/verify", headers={"Authorization": "Bearer admin_01"})
    assert res.status_code == 200
    assert res.json()["ok"] is True
    assert res.json()["length"] == 2
    
    # Tamper with the first entry
    with open(REGISTRY_FILE, 'r+') as f:
        registry = json.load(f)
        registry["audit"][0]["data"] = {"tampered": True}
        f.seek(0)
        json.dump(registry, f, indent=2)
        f.truncate()
        
    # Verify should now fail
    res2 = client.get("/governance/audit/verify", headers={"Authorization": "Bearer admin_01"})
    assert res2.status_code == 200
    assert res2.json()["ok"] is False

def test_governance_corridor_endpoints():
    response = client.get("/corridor/version", headers={"Authorization": "Bearer op_01"})
    assert response.status_code == 200
    
def test_governance_mode_endpoints():
    response = client.get("/mode/current", headers={"Authorization": "Bearer op_01"})
    assert response.status_code == 200
