from fastapi.testclient import TestClient
import os
import json
import pytest

os.environ["LLM_DETERMINISTIC"] = "true"
os.environ["GOVERNANCE_BASE"] = "http://localhost:8001"

from services.llm.main import app
from services.llm.services.claim_checker import extract_numbers, check_numbers_in_text, check_forbidden_phrases, build_safety_report

client = TestClient(app)

def test_health():
    response = client.get("/llm/health")
    assert response.status_code == 200
    data = response.json()
    assert "uptime_sec" in data
    assert data["provider"] in ["gemini", "openai", "anthropic"]

def test_explain_proposal_unauthorized():
    payload = {
        "proposal": {
            "id": "prop-0007",
            "delta": {},
            "evidence": {
                "summary": "",
                "metrics": {"energy_delta_pct": 0, "quality_issues": 0, "yield_mean": 0},
                "kpi_window": [],
                "counterfactuals": {}
            },
            "context": {}
        },
        "ask": {
            "audience": "operator",
            "tone": "concise",
            "sections": ["rationale"]
        }
    }
    response = client.post("/llm/proposal/explain", json=payload)
    assert response.status_code == 401

def test_explain_proposal():
    payload = {
        "proposal": {
            "id": "prop-0007",
            "delta": {"temperature_upper": -0.5},
            "evidence": {
                "summary": "Energy decreased while quality stable",
                "metrics": {"energy_delta_pct": -3.8, "quality_issues": 0, "yield_mean": 90.6},
                "kpi_window": ["B10", "B11", "B12"],
                "counterfactuals": {}
            },
            "context": {"corridor_version": "v3"}
        },
        "ask": {
            "audience": "operator",
            "tone": "concise",
            "sections": ["rationale"]
        }
    }
    
    response = client.post(
        "/llm/proposal/explain",
        json=payload,
        headers={"Authorization": "Bearer eng_01"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "explanation" in data
    assert "safety_report" in data
    assert data["proposal_id"] == "prop-0007"

def test_validate_proposal_overclaim():
    payload = {
        "proposal": {
            "id": "prop-0007",
            "delta": {},
            "evidence": {
                "summary": "",
                "metrics": {"energy_delta_pct": -3.8, "quality_issues": 0, "yield_mean": 90.6},
                "kpi_window": [],
                "counterfactuals": {}
            },
            "context": {}
        },
        "narrative": {
            "rationale": "It saves -5.0 energy!",
            "risks": [],
            "assumptions": []
        },
        "rules": {
            "tolerances": {"energy_delta_pct": 0.2},
            "forbidden_phrases": ["guarantee"]
        }
    }
    
    response = client.post(
        "/llm/proposal/validate",
        json=payload,
        headers={"Authorization": "Bearer eng_01"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["validation"]["status"] in ["warn", "fail"]
    assert len(data["validation"]["issues"]) > 0

def test_evidence_summary():
    payload = {
        "snapshot": {
            "active_version": "v3",
            "bounds": {"temperature": {"lower": 145, "upper": 154.5}, "flow": {"lower": 10, "upper": 14.2}},
            "recent_kpis": [
                {"batch_id": "B10", "energy_kwh": 96.4, "yield_pct": 91.2, "quality_deviation": False}
            ],
            "proposals": [],
            "system_metrics": {}
        },
        "style": "operator",
        "length": "short"
    }
    
    response = client.post(
        "/llm/evidence/summary",
        json=payload,
        headers={"Authorization": "Bearer op_01"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "safety_report" in data

def test_claim_checker_logic():
    text = "The energy improved by -4.0 and we guarantee it works 100 times."
    metrics = {"energy_delta_pct": -3.8}
    tolerances = {"energy_delta_pct": 0.1}
    
    issues = check_numbers_in_text(text, metrics, tolerances)
    assert len(issues) > 0
    
    forbidden = check_forbidden_phrases(text, ["guarantee", "perfect"])
    assert "guarantee" in forbidden
    
    safety = build_safety_report(issues, forbidden)
    assert safety["data_usage_ok"] == False
    assert safety["hallucination_risk"] in ["medium", "high"]
