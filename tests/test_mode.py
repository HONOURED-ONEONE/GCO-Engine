import pytest
from fastapi.testclient import TestClient
import os
import json
import shutil
from app.api.main import app
from app.api.utils.io import REGISTRY_FILE, init_files

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_teardown():
    # Setup: Ensure fresh registry for tests
    if os.path.exists(REGISTRY_FILE):
        os.remove(REGISTRY_FILE)
    init_files()
    yield
    # Teardown: Clean up
    if os.path.exists(REGISTRY_FILE):
        os.remove(REGISTRY_FILE)

def test_mode_policy_contract():
    """ensures both modes exist and weights sum to 1.0"""
    response = client.get("/mode/policy")
    assert response.status_code == 200
    data = response.json()
    assert len(data["allowed_modes"]) == 2
    
    for mode in data["allowed_modes"]:
        weights = mode["weights"]
        total = sum(weights.values())
        assert pytest.approx(total) == 1.0
        assert mode["id"] in ["sustainability_first", "production_first"]

def test_mode_current():
    response = client.get("/mode/current")
    assert response.status_code == 200
    data = response.json()
    assert "mode" in data
    assert "weights" in data
    assert "changed_at" in data

def test_mode_set_valid():
    # Set to production_first
    response = client.post("/mode/set", json={"mode": "production_first"})
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "production_first"
    assert data["changed"] is True
    assert data["weights"]["energy"] == 0.25
    
    # Verify persistence in registry
    with open(REGISTRY_FILE, 'r') as f:
        registry = json.load(f)
        assert registry["last_mode"] == "production_first"
        assert len(registry["audit"]["mode_changes"]) >= 1

def test_mode_set_invalid():
    response = client.post("/mode/set", json={"mode": "invalid_mode"})
    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["error"] == "invalid_mode"

def test_mode_idempotency():
    # Set once
    client.post("/mode/set", json={"mode": "production_first"})
    
    # Set again
    response = client.post("/mode/set", json={"mode": "production_first"})
    assert response.status_code == 200
    data = response.json()
    assert data["changed"] is False
    assert data["message"] == "No change"
    
    # Audit log should not have grown from the second call
    with open(REGISTRY_FILE, 'r') as f:
        registry = json.load(f)
        # Should only have one change entry if we started from sustainability_first
        # Actually init_files sets it to sustainability_first, so setting to production_first adds 1.
        # Second call to production_first should not add more.
        assert len(registry["audit"]["mode_changes"]) == 1

def test_concurrent_writes():
    import threading
    import time
    
    def set_mode_task(mode):
        client.post("/mode/set", json={"mode": mode})

    threads = []
    for i in range(10):
        mode = "production_first" if i % 2 == 0 else "sustainability_first"
        t = threading.Thread(target=set_mode_task, args=(mode,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    # Final state should be valid JSON and readable
    response = client.get("/mode/current")
    assert response.status_code == 200
