import os

GOVERNANCE_BASE = os.environ.get("GOVERNANCE_BASE", "http://localhost:8001")
OPTIMIZER_BASE = os.environ.get("OPTIMIZER_BASE", "http://localhost:8002")
MONOLITH_BASE = os.environ.get("MONOLITH_BASE", "http://localhost:8003")
LLM_BASE = os.environ.get("LLM_BASE", "http://localhost:8004")
KPI_BASE = os.environ.get("KPI_BASE", "http://localhost:8005")
OPA_BASE = os.environ.get("OPA_BASE", "http://localhost:8181")

GATEWAY_JWKS_URL = os.environ.get("GATEWAY_JWKS_URL")
GATEWAY_JWT_SECRET = os.environ.get("GATEWAY_JWT_SECRET", "secret")
GATEWAY_VALIDATE_AUD = os.environ.get("GATEWAY_VALIDATE_AUD", "false").lower() == "true"
GATEWAY_SYSTEM_TOKEN = os.environ.get("GATEWAY_SYSTEM_TOKEN", "system_01")
GATEWAY_LIMITS = os.environ.get("GATEWAY_LIMITS", "")
