import os

GOVERNANCE_BASE = os.environ.get("GOVERNANCE_BASE", "http://localhost:8001")
OPTIMIZER_BASE = os.environ.get("OPTIMIZER_BASE", "http://localhost:8002")
LLM_BASE = os.environ.get("LLM_BASE", "http://localhost:8004")
KPI_BASE = os.environ.get("KPI_BASE", "http://localhost:8005")
POLICY_BASE = os.environ.get("POLICY_BASE", "http://localhost:8006")
TWIN_BASE = os.environ.get("TWIN_BASE", "http://localhost:8007")
PILOT_BASE = os.environ.get("PILOT_BASE", "http://localhost:8007")
EVIDENCE_BASE = os.environ.get("EVIDENCE_BASE", "http://localhost:8008")
OT_BASE = os.environ.get("OT_BASE", "http://localhost:8009")
OPA_BASE = os.environ.get("OPA_BASE", "http://localhost:8181")

GATEWAY_JWKS_URL = os.environ.get("GATEWAY_JWKS_URL")
GATEWAY_JWT_SECRET = os.environ.get("GATEWAY_JWT_SECRET", "secret")
GATEWAY_VALIDATE_AUD = os.environ.get("GATEWAY_VALIDATE_AUD", "false").lower() == "true"
GATEWAY_SYSTEM_TOKEN = os.environ.get("GATEWAY_SYSTEM_TOKEN", "system_01")
GATEWAY_LIMITS = os.environ.get("GATEWAY_LIMITS", "")

SECURITY_MODE = os.environ.get("SECURITY_MODE", "dev").lower()
JWT_ISSUER = os.environ.get("JWT_ISSUER", "gco-engine")
JWT_AUDIENCE = os.environ.get("JWT_AUDIENCE", "gco-services")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "RS256")
JWKS_CACHE_TTL = int(os.environ.get("JWKS_CACHE_TTL", "3600"))
