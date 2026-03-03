import pytest
import os
import pandas as pd
from fastapi.testclient import TestClient
from app.api.main import app
from app.api.utils.io import init_files, BASE_DATA_DIR, REGISTRY_FILE

client = TestClient(app)
AUTH_HEADERS = {"Authorization": "Bearer admin_01"}

@pytest.fixture(scope="module", autouse=True)
def setup_data():
    if os.path.exists(REGISTRY_FILE):
        os.remove(REGISTRY_FILE)
    init_files()
    # Create a dummy batch B001 with values within corridor bounds [145, 155]
    batch_dir = os.path.join(BASE_DATA_DIR, "batches")
    os.makedirs(batch_dir, exist_ok=True)
    batch_path = os.path.join(batch_dir, "B001.csv")
    df = pd.DataFrame([
        {"ts": "2025-01-01T00:00:00", "temperature": 150.0, "flow": 12.0},
        {"ts": "2025-01-01T00:00:10", "temperature": 152.0, "flow": 13.0},
        {"ts": "2025-01-01T00:00:20", "temperature": 148.0, "flow": 11.0},
    ])
    df.to_csv(batch_path, index=False)
    yield

def test_optimize_recommend_basic():
    response = client.post("/optimize/recommend", json={
        "batch_id": "B001",
        "ts": "2025-01-01T00:00:00"
    }, headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "setpoints" in data
    assert "temperature" in data["setpoints"]
    assert "flow" in data["setpoints"]
    assert data["compute_ms"] >= 0
    assert "rationale" in data

def test_optimize_within_bounds():
    response = client.post("/optimize/recommend", json={
        "batch_id": "B001",
        "ts": "2025-01-01T00:00:00"
    }, headers=AUTH_HEADERS)
    data = response.json()
    setpoints = data["setpoints"]
    constraints = data["constraints"]
    
    # State bounds
    assert constraints["temperature"]["lower"] <= setpoints["temperature"] <= constraints["temperature"]["upper"]
    assert constraints["flow"]["lower"] <= setpoints["flow"] <= constraints["flow"]["upper"]

def test_objective_weights_mode_switch():
    # Ensure starting from sustainability
    r = client.post("/mode/set", json={"mode": "sustainability_first"}, headers=AUTH_HEADERS)
    assert r.status_code == 200
    
    res1 = client.post("/optimize/recommend", json={"batch_id": "B001", "ts": "2025-01-01T00:00:00"}, headers=AUTH_HEADERS)
    assert res1.status_code == 200
    w1 = res1.json()["objective_weights"]
    
    # Production mode
    r = client.post("/mode/set", json={"mode": "production_first"}, headers=AUTH_HEADERS)
    assert r.status_code == 200
    
    res2 = client.post("/optimize/recommend", json={"batch_id": "B001", "ts": "2025-01-01T00:00:00"}, headers=AUTH_HEADERS)
    assert res2.status_code == 200
    w2 = res2.json()["objective_weights"]
    
    assert w1 != w2
    # Sustainability energy weight should be 0.6, Production 0.25
    assert w1["energy"] == 0.6
    assert w2["energy"] == 0.25

def test_preview_length_and_timestamps():
    response = client.get("/optimize/preview", params={"batch_id": "B001", "window": 2}, headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert len(data["points"]) == 2
    assert data["points"][0]["ts"] == "2025-01-01T00:00:00"
    assert data["points"][1]["ts"] == "2025-01-01T00:00:10"

def test_health_endpoint():
    client.post("/optimize/recommend", json={"batch_id": "B001", "ts": "2025-01-01T00:00:00"}, headers=AUTH_HEADERS)
    response = client.get("/optimize/health", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["calls_total"] >= 1
    assert "cache" in data

def test_ot_writeback_guarded():
    # Not armed
    r1 = client.post("/optimize/recommend", json={"batch_id": "B001", "ts": "2025-01-01T00:00:00", "write_back": True}, headers=AUTH_HEADERS)
    assert r1.json()["ot_status"]["success"] == False
    
    # Arm OT
    client.post("/ot/arm", json={"batch_id": "B001", "duration_sec": 60}, headers=AUTH_HEADERS)
    
    # Now success (shadow by default, but successful write attempt)
    r2 = client.post("/optimize/recommend", json={"batch_id": "B001", "ts": "2025-01-01T00:00:00", "write_back": True}, headers=AUTH_HEADERS)
    assert r2.json()["ot_status"]["success"] == True
