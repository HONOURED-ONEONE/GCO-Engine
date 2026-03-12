import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import json

from services.evidence.main import app

@pytest.fixture
def evidence_dir():
    with tempfile.TemporaryDirectory() as td:
        yield td

@pytest.fixture
def client(evidence_dir):
    with patch("services.evidence.services.collect.EVIDENCE_DIR", evidence_dir), \
         patch("services.evidence.routers.evidence.EVIDENCE_DIR", evidence_dir), \
         patch("services.evidence.services.pack._ensure_dir", return_value=None):
        yield TestClient(app)

def test_health(client):
    headers = {"X-User-Id": "admin_01"}
    resp = client.get("/evidence/health", headers=headers)
    assert resp.status_code == 200
    assert "uptime_sec" in resp.json()

@patch("services.evidence.services.collect.EvidenceCollector.get_json")
@patch("services.evidence.services.collect.EvidenceCollector.post_audit")
def test_snapshot(mock_audit, mock_get, client):
    mock_get.return_value = {"version": "v1", "bounds": {"b1": {"min":0, "max":1}}}
    headers = {"X-User-Id": "op_01"}
    resp = client.get("/evidence/snapshot", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "run_id" in data
    assert data["active_version"] == "v1"
    mock_audit.assert_called()

@patch("services.evidence.services.collect.EvidenceCollector.get_json")
@patch("services.evidence.services.collect.EvidenceCollector.post_audit")
def test_capture(mock_audit, mock_get, client):
    mock_get.return_value = {"version": "v1", "bounds": {"b1": {"min":0, "max":1}}}
    headers = {"X-User-Id": "eng_01"}
    resp = client.post("/evidence/capture", json={"run_id": None, "charts": ["bands", "objectives"]}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert len(data["charts"]) == 2

@patch("services.evidence.services.collect.EvidenceCollector.get_json")
@patch("services.evidence.services.collect.EvidenceCollector.post_audit")
def test_pack(mock_audit, mock_get, client):
    mock_get.return_value = {"version": "v1", "bounds": {"b1": {"min":0, "max":1}}}
    headers = {"X-User-Id": "eng_01"}
    resp = client.post("/evidence/pack", json={"run_id": None, "title": "Test"}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert "run_report.pdf" in data["pdf"]
    assert ".zip" in data["zip"]

@patch("services.evidence.services.collect.EvidenceCollector.get_json")
def test_files(mock_get, client):
    mock_get.return_value = {"version": "v1"}
    headers = {"X-User-Id": "eng_01"}
    pack_resp = client.post("/evidence/pack", json={"run_id": None}, headers=headers)
    run_id = pack_resp.json()["run_id"]
    
    files_resp = client.get(f"/evidence/files?run_id={run_id}", headers=headers)
    assert files_resp.status_code == 200
    data = files_resp.json()
    assert len(data["files"]) > 0
