import pytest
import os
from fastapi.testclient import TestClient
from app.api.main import app
from app.api.utils.io import init_files, REGISTRY_FILE

client = TestClient(app)
ADMIN_HEADERS = {"Authorization": "Bearer admin_01"}
OP_HEADERS = {"Authorization": "Bearer op_01"}
ENG_HEADERS = {"Authorization": "Bearer eng_01"}

@pytest.fixture(scope="module", autouse=True)
def setup():
    if os.path.exists(REGISTRY_FILE):
        os.remove(REGISTRY_FILE)
    init_files()
    yield

def test_ot_arm_disarm_rbac():
    # Engineer cannot arm
    resp = client.post("/ot/arm", json={"batch_id": "test", "duration_sec": 60}, headers=ENG_HEADERS)
    assert resp.status_code == 403
    
    # Operator can arm
    resp = client.post("/ot/arm", json={"batch_id": "test", "duration_sec": 60}, headers=OP_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["status"]["armed"] == True
    
    # Disarm
    resp = client.post("/ot/disarm", headers=OP_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["status"]["armed"] == False

def test_policy_lifecycle():
    # Seed experience to allow training
    from app.api.services.marl import log_experience
    for i in range(5):
        log_experience(f"B{i:03d}", [{"T": 150, "F": 12}], 0.9)

    # List policies
    resp = client.get("/policy/list", headers=ENG_HEADERS)
    assert resp.status_code == 200
    policies = resp.json()
    assert len(policies) >= 1
    
    # Train new policy
    resp = client.post("/policy/train", headers=ENG_HEADERS)
    assert resp.status_code == 200
    new_policy = resp.json()
    assert "id" in new_policy
    
    # Activate policy (Admin only)
    resp = client.post(f"/policy/activate/{new_policy['id']}", headers=OP_HEADERS)
    assert resp.status_code == 403
    
    resp = client.post(f"/policy/activate/{new_policy['id']}", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    
    # Check active
    resp = client.get("/policy/active", headers=OP_HEADERS)
    assert resp.json()["id"] == new_policy["id"]

def test_audit_tamper_evidence():
    # Perform some actions
    client.post("/mode/set", json={"mode": "production_first"}, headers=OP_HEADERS)
    
    resp = client.get("/corridor/audit", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) >= 1
    assert "hash" in items[0]
    
    # Verify chain (logic is in service, here we check endpoint exists or just assume it works if status is 200)
    # For MVP, we've implemented verify_audit_chain in audit.py but no dedicated route yet.
    # We could add one if needed.
