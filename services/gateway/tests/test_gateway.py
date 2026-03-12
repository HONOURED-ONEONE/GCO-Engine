import pytest
from fastapi.testclient import TestClient
from services.gateway.main import app
from unittest.mock import AsyncMock

client = TestClient(app)

def test_gateway_status(monkeypatch):
    mock_get = AsyncMock()
    # Mocking status check responses
    class MockResp:
        status_code = 200
    mock_get.return_value = MockResp()
    monkeypatch.setattr("services.gateway.router.client.get", mock_get)
    
    response = client.get("/gateway/status")
    assert response.status_code == 200
    assert response.json()["governance"] == "up"

def test_missing_auth():
    response = client.get("/twin/scenarios")
    assert response.status_code == 401

def test_invalid_auth():
    response = client.get("/twin/scenarios", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401

def test_proxy_allow(monkeypatch):
    mock_req = AsyncMock()
    class MockResp:
        status_code = 200
        content = b'{"msg": "ok"}'
        headers = {}
    mock_req.return_value = MockResp()
    
    mock_eval = AsyncMock()
    mock_eval.return_value = (True, {"X-Policy-Version": "v1"})
    
    monkeypatch.setattr("services.gateway.router.client.request", mock_req)
    monkeypatch.setattr("services.gateway.router.evaluate", mock_eval)
    
    response = client.get("/twin/scenarios", headers={"Authorization": "Bearer admin_01"})
    assert response.status_code == 200

def test_proxy_deny(monkeypatch):
    mock_eval = AsyncMock()
    mock_eval.return_value = (False, {})
    monkeypatch.setattr("services.gateway.router.evaluate", mock_eval)
    
    response = client.post("/corridor/approve", headers={"Authorization": "Bearer op_01"}, json={"test": "data"})
    assert response.status_code == 403
