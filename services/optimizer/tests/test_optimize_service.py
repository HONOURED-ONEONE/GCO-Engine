import pytest
import os
import json
import time
from fastapi.testclient import TestClient
from services.optimizer.main import app
from services.optimizer.clients.governance_client import governance_client
from unittest.mock import patch

client = TestClient(app)

MOCK_STATE = {
    "active_version": "v1",
    "bounds": {
        "temperature": {"lower": 140.0, "upper": 160.0},
        "flow": {"lower": 5.0, "upper": 15.0}
    },
    "mode": "test_mode",
    "weights": {"energy": 0.5, "quality": 0.3, "yield": 0.2}
}

class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception("HTTP Error")

@pytest.fixture(autouse=True)
def mock_governance():
    with patch("httpx.get") as mock_get:
        mock_get.return_value = MockResponse(MOCK_STATE, 200)
        yield mock_get

@pytest.fixture(autouse=True)
def setup_test_data():
    os.makedirs("data/batches", exist_ok=True)
    with open("data/batches/test_batch.csv", "w") as f:
        f.write("ts,temperature,flow\n")
        f.write("2026-03-03T10:00:00Z,150.0,10.0\n")
        f.write("2026-03-03T10:01:00Z,151.0,11.0\n")
    yield
    os.remove("data/batches/test_batch.csv")

def test_health():
    res = client.get("/optimize/health", headers={"Authorization": "Bearer admin_01"})
    assert res.status_code == 200
    data = res.json()
    assert "uptime_sec" in data

def test_caching(mock_governance):
    governance_client._cache = None
    governance_client._cache_time = 0
    governance_client.hits = 0
    governance_client.misses = 0

    client.get("/optimize/health", headers={"Authorization": "Bearer admin_01"})
    # Only hits governance client when actual context is needed by recommend/preview
    
    # First call misses cache
    res1 = client.post("/optimize/recommend", headers={"Authorization": "Bearer admin_01"}, json={
        "batch_id": "test_batch",
        "ts": "2026-03-03T10:00:00Z"
    })
    assert res1.status_code == 200
    assert governance_client.misses == 1

    # Second call hits cache
    res2 = client.post("/optimize/recommend", headers={"Authorization": "Bearer admin_01"}, json={
        "batch_id": "test_batch",
        "ts": "2026-03-03T10:00:00Z"
    })
    assert res2.status_code == 200
    assert governance_client.hits == 1

def test_recommend():
    res = client.post("/optimize/recommend", headers={"Authorization": "Bearer admin_01"}, json={
        "batch_id": "test_batch",
        "ts": "2026-03-03T10:00:00Z",
        "hints": {"restraint": True}
    })
    assert res.status_code == 200
    data = res.json()
    assert data["within_bounds"] is True
    assert "setpoints" in data
    assert data["constraints"] == MOCK_STATE["bounds"]
    assert data["objective_weights"] == MOCK_STATE["weights"]
    
def test_preview():
    res = client.get("/optimize/preview?batch_id=test_batch&window=2", headers={"Authorization": "Bearer admin_01"})
    assert res.status_code == 200
    data = res.json()
    assert len(data["points"]) == 2
    assert data["horizon"] == 2
