import pytest
import time
from fastapi.testclient import TestClient
from app.api.main import app
from app.api.services.twin import twin_service
from app.api.services.pilot import pilot_service

client = TestClient(app)

def test_twin_lifecycle():
    # Start Twin
    resp = client.post("/twin/start", json={"scenario_id": "S-NORMAL", "seed": 1234})
    assert resp.status_code == 200
    data = resp.json()
    assert data["twin_session_id"] == "tw-1234"
    assert data["status"] == "running"
    
    # Get Status
    resp = client.get("/twin/status")
    assert resp.status_code == 200
    assert resp.json()["status"] == "running"
    
    # Stop Twin
    resp = client.post("/twin/stop", json={"twin_session_id": "tw-1234"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "stopped"

@pytest.mark.asyncio
async def test_pilot_shadow_mode():
    # Setup Twin
    client.post("/twin/start", json={"scenario_id": "S-NORMAL", "seed": 4269})
    
    # Start Pilot
    resp = client.post("/pilot/start", json={
        "pilot_id": "P-TEST",
        "twin_session_id": "tw-4269",
        "schedule": {"start": "now", "end": "1h"},
        "mode": "sustainability_first"
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "running"
    
    # Wait a bit for some steps
    time.sleep(1)
    
    # Check Health
    resp = client.get("/pilot/health?pilot_id=P-TEST")
    assert resp.status_code == 200
    health = resp.json()
    assert health["uptime_sec"] >= 1
    
    # Check Snapshot
    resp = client.get("/pilot/snapshot?pilot_id=P-TEST")
    assert resp.status_code == 200
    snapshot = resp.json()
    assert snapshot["pilot_id"] == "P-TEST"
    assert len(snapshot["history_tail"]) > 0
    
    # Stop Pilot
    client.post("/pilot/stop", json={"pilot_id": "P-TEST"})
    client.post("/twin/stop", json={"twin_session_id": "tw-4269"})

def test_roi_calculator_sane():
    from app.pilot.roi import ROICalculator
    calc = ROICalculator()
    baseline = [{"energy_kwh": 50.0}, {"energy_kwh": 52.0}]
    shadow = [{"energy_kwh": 45.0}, {"energy_kwh": 46.0}]
    
    res = calc.calculate_savings(baseline, shadow)
    assert res["delta_kwh_per_batch"] > 0
    assert res["annualized_savings_est"] > 0
    assert len(res["ci_90"]) == 2
