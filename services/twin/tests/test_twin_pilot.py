import pytest
from fastapi.testclient import TestClient
from ..main import app
from ..services.scenarios import manager
from ..services.simulator import Simulator
from ..models.schemas import ScenarioConfig

client = TestClient(app)

# Helper to ensure we have scenarios for tests
@pytest.fixture(autouse=True)
def ensure_scenarios():
    if "S-TEST" not in manager.scenarios:
        # Add a dummy scenario for testing
        dummy = ScenarioConfig(
            id="S-TEST",
            name="Test Scenario",
            description="For pytest",
            initial_state={"temperature": 25.0, "flow": 10.0},
            parameters={"thermal_inertia": 0.5, "yield_base": 100.0, "temp_optimal": 70.0, "quality_limit": 90.0},
            disturbance_model={"noise": 0.0, "drift": 0.0},
            kpi_formulas={}
        )
        manager.scenarios["S-TEST"] = dummy

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "twin-service running" in response.json()["message"]

def test_list_scenarios():
    response = client.get("/twin/scenarios")
    assert response.status_code == 200
    assert "S-TEST" in response.json()["scenarios"]

def test_twin_run_deterministic():
    req = {"scenario_id": "S-TEST", "horizon": 10, "seed": 42}
    resp1 = client.post("/twin/run", json=req)
    resp2 = client.post("/twin/run", json=req)
    
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json()["timeseries"] == resp2.json()["timeseries"]
    assert resp1.json()["kpis"] == resp2.json()["kpis"]

def test_counterfactual():
    req = {
        "scenario_id": "S-TEST",
        "corridor_delta": {"temperature_upper": -5.0},
        "weight_delta": {"energy": 0.1},
        "seed": 42
    }
    response = client.post("/twin/counterfactual", json=req)
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "expected_energy_delta_pct" in data["metrics"]

def test_pilot_lifecycle():
    # Start pilot
    start_req = {
        "pilot_id": "P-TEST",
        "scenario_id": "S-TEST",
        "mode": "balanced",
        "horizon_minutes": 5,
        "seed": 42
    }
    response = client.post("/pilot/start", json=start_req)
    assert response.status_code == 200
    
    # Health check
    response = client.get("/pilot/health?pilot_id=P-TEST")
    assert response.status_code == 200
    assert response.json()["pilot_id"] == "P-TEST"
    
    # Snapshot
    response = client.get("/pilot/snapshot?pilot_id=P-TEST")
    assert response.status_code == 200
    assert "timeseries" in response.json()
    
    # Stop
    response = client.post("/pilot/stop", json={"pilot_id": "P-TEST"})
    assert response.status_code == 200
    assert response.json()["status"] == "stopped"
