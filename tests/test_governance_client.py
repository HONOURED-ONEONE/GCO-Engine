import pytest
import os
from unittest.mock import patch, MagicMock
from app.api.clients.governance_client import GovernanceClient

@pytest.fixture
def mock_local_env():
    # Ensure no external base URL
    if "GOVERNANCE_BASE" in os.environ:
        del os.environ["GOVERNANCE_BASE"]

@pytest.fixture
def mock_remote_env(monkeypatch):
    monkeypatch.setenv("GOVERNANCE_BASE", "http://mock-governance:8001")

def test_client_local_fallback(mock_local_env):
    with patch("app.api.clients.governance_client.get_active_corridor", return_value=("v1", {"bounds": {"a": 1}})), \
         patch("app.api.clients.governance_client.get_current_mode_data", return_value={"mode": "prod", "weights": {"b": 2}}):
        client = GovernanceClient()
        v, bounds, mode, weights = client.get_active()
        assert v == "v1"
        assert bounds == {"a": 1}
        assert mode == "prod"
        assert weights == {"b": 2}

@patch("app.api.clients.governance_client.requests.get")
def test_client_remote_active(mock_get, mock_remote_env):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "active_version": "v2",
        "bounds": {"c": 3},
        "last_mode": "sustain",
        "last_mode_weights": {"d": 4}
    }
    mock_get.return_value = mock_resp
    
    client = GovernanceClient(token="op_01")
    v, bounds, mode, weights = client.get_active()
    
    mock_get.assert_called_once_with("http://mock-governance:8001/governance/active", headers={"Authorization": "Bearer op_01"})
    assert v == "v2"
    assert bounds == {"c": 3}
    assert mode == "sustain"
    assert weights == {"d": 4}

@patch("app.api.clients.governance_client.requests.post")
def test_client_remote_audit(mock_post, mock_remote_env):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"hash": "abc"}
    mock_post.return_value = mock_resp
    
    client = GovernanceClient(token="admin_01")
    hash_val = client.audit_ingest("test", {"k": "v"})
    
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "http://mock-governance:8001/governance/audit/ingest"
    assert kwargs["json"]["event_type"] == "test"
    assert kwargs["json"]["user_id"] == "admin_01"
    assert hash_val == "abc"
