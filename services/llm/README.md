# GCO LLM Reasoning Sidecar

This service acts as an early, strictly READ-ONLY LLM reasoning sidecar.
It is responsible for explaining and validating proposals, as well as generating evidence-pack summaries.
It **never** changes control-plane state or calls OT modification endpoints.

## Endpoints
- `POST /llm/proposal/explain`: Explain a proposal (Engineer/Admin)
- `POST /llm/proposal/validate`: Validate a proposal against overclaims (Engineer/Admin)
- `POST /llm/evidence/summary`: Summarize a pilot snapshot (Operator/Engineer/Admin)
- `GET /llm/health`: Get observability metrics and configuration

## Env Vars
- `PROVIDER`: e.g. "gemini", "openai", "anthropic"
- `MODEL_ID`: e.g. "gemini-1.5-pro"
- `LLM_API_KEY`: API Key
- `LLM_DETERMINISTIC`: If "true", will use seeded stubs instead of making external calls (for tests)
- `GOVERNANCE_BASE`: Governance API base URL

## Security
This microservice validates JWTs. Additionally, OPA acts as a centralized authorization server via the Gateway.

## What it cannot do
- Modifying rules
- Modifying corridors
- Acting as a closed-loop controller
