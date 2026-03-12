import pytest
from fastapi.testclient import TestClient
import os
import tempfile
import json
from unittest.mock import patch

# Setup a temporary store path before importing the app
temp_dir = tempfile.TemporaryDirectory()
temp_store_path = os.path.join(temp_dir.name, "kpi_store_test.json")
os.environ["KPI_STORE_PATH"] = temp_store_path

from services.kpi.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_store():
    # Reset store before each test
    with open(temp_store_path, "w") as f:
        json.dump({"items": []}, f)
    yield

def test_health_endpoint():
    response = client.get("/kpi/health", headers={"Authorization": "Bearer admin_01"})
    assert response.status_code == 200
    data = response.json()
    assert "uptime_sec" in data
    assert data["store_size"] == 0

@patch("services.kpi.routers.kpi.post_audit")
@patch("services.kpi.routers.kpi.maybe_notify")
def test_ingest_and_recent(mock_notify, mock_audit):
    # 1. Ingest new KPI
    payload = {
        "batch_id": "b1",
        "energy_kwh": 50.0,
        "yield_pct": 95.0,
        "quality_deviation": False
    }
    response = client.post("/kpi/ingest", json=payload, headers={"Authorization": "Bearer op_01"})
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["message"] == "ingested"
    assert data["anomaly_flag"] is False
    assert data["batch_id"] == "b1"
    
    # 2. Re-ingest same batch id with diff values
    payload["energy_kwh"] = 55.0
    response = client.post("/kpi/ingest", json=payload, headers={"Authorization": "Bearer op_01"})
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "updated"
    assert data["batch_id"] == "b1"
    
    # 3. Check recent returns items in correct order
    response = client.get("/kpi/recent?limit=2", headers={"Authorization": "Bearer op_01"})
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["items"][0]["energy_kwh"] == 55.0
    assert data["items"][0]["updated_at"] is not None

def test_anomaly_rules():
    # Rule A: quality_deviation
    payload = {
        "batch_id": "b_qual",
        "energy_kwh": 50.0,
        "yield_pct": 95.0,
        "quality_deviation": True
    }
    response = client.post("/kpi/ingest", json=payload, headers={"Authorization": "Bearer op_01"})
    assert response.json()["anomaly_flag"] is True

    # Rule B: yield < 80
    payload = {
        "batch_id": "b_yield",
        "energy_kwh": 50.0,
        "yield_pct": 79.0,
        "quality_deviation": False
    }
    response = client.post("/kpi/ingest", json=payload, headers={"Authorization": "Bearer op_01"})
    assert response.json()["anomaly_flag"] is True

    # Rule C: energy outside rolling p10-p90
    # First, ingest some normal batches
    for i in range(10):
        client.post("/kpi/ingest", json={
            "batch_id": f"b_norm_{i}",
            "energy_kwh": 50.0 + (i % 2), # 50 or 51
            "yield_pct": 95.0,
            "quality_deviation": False
        }, headers={"Authorization": "Bearer op_01"})
        
    # Now ingest out of band
    payload = {
        "batch_id": "b_energy",
        "energy_kwh": 100.0,
        "yield_pct": 95.0,
        "quality_deviation": False
    }
    response = client.post("/kpi/ingest", json=payload, headers={"Authorization": "Bearer op_01"})
    assert response.json()["anomaly_flag"] is True

def test_stats_endpoint():
    response = client.get("/kpi/stats", headers={"Authorization": "Bearer admin_01"})
    assert response.status_code == 200
    data = response.json()
    assert "p10_p90" in data
    assert "anomaly_count" in data
