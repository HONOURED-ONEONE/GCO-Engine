from fastapi.testclient import TestClient
from unittest.mock import patch
from ..main import app

client = TestClient(app)

def test_health():
    res = client.get("/policy/health", headers={"Authorization": "admin_01"})
    assert res.status_code == 200

@patch("services.policy.clients.governance_client.requests.post")
def test_maybe_propose(mock_post):
    mock_resp = mock_post.return_value
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"proposal_id": "prop-0009"}
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
    assert data["proposed"] is True
    assert data["proposal_id"] == "prop-0009"

def test_train_and_activate():
    train_req = {
        "context": {"corridor_version": "v3", "mode": "sustainability_first"},
        "epochs": 1
    }
    res_train = client.post("/policy/train", json=train_req, headers={"Authorization": "eng_01"})
    assert res_train.status_code == 200
    p_id = res_train.json().get("policy_id")
    res_act = client.post(f"/policy/activate/{p_id}", headers={"Authorization": "admin_01"})
    assert res_act.status_code == 200
