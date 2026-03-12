# Golden Corridor Optimization Engine (Track B)

Phase 5: Judge Demo Automation & Evidence Pack

## 🚀 Judge Quickstart (Deterministic Offline Demo)

1.  **Install Dependencies**:
    ```bash
    make install
    ```

2.  **Start API**:
    ```bash
    make api
    ```
    *(In a separate terminal)*

3.  **Start UI**:
    ```bash
    make ui
    ```
    *(Open http://localhost:8501)*

4.  **Run Full Automated Demo**:
    ```bash
    make judge-demo
    ```
    *(This seeds all scenarios, runs the loop, captures charts, and packs evidence)*

5.  **Review Evidence Pack**:
    Open `evidence/run_report.pdf` or examine the generated `gco_evidence_*.zip`.

## 📦 Key Capabilities (Phase 5)

- **Scenario S1: Sustainability-First**: Energy consumption drops 3%+, triggering a MARL proposal to tighten temperature upper bounds.
- **Scenario S2: Quality Guardrail**: Sporadic quality deviations trigger a widening of temperature bounds for safety.
- **Scenario S3: Yield Boost**: Trending yields below 85% trigger an increase in flow upper limits.
- **Evidence Pack**: Self-contained ZIP with PNG charts, KPI CSVs, Version JSONs, and an auto-generated PDF summary.
- **Tamper-Evident Audit**: Chained SHA-256 hashes for all system actions (mode changes, approvals, writes).
- **Safety-First NMPC**: Real-time Nonlinear Model Predictive Control (CasADi) with corridor constraint enforcement.

## 🛡️ Stage 0: Governance Control Plane
We are actively refactoring towards a microservices architecture. Stage 0 establishes a dedicated Governance Control Plane.
- **Run Governance Service**: `make governance` (runs on port 8001)
- **Run Full Stack (Docker)**: `make up`
- **Smoke Test**: `make stage0-smoke`

The new `governance-service` exclusively owns bounds, policies, and the tamper-evident audit chain. To maintain backwards compatibility and preserve the deterministic demo, the monolith currently proxies or mirrors these endpoints until full decoupling is completed.

## 🛡️ Stage 1: PEP Gateway & Optimizer Service
### PEP Gateway
A dedicated API Gateway that serves as a Zero-Trust Policy Enforcement Point (PEP), backed by Open Policy Agent (OPA).
- **Single public entrypoint**: Gateway on `:8000`.
- **Zero-Trust Edge**: Enforces AuthN (JWT) and AuthZ (via external OPA PDP).

### Optimizer Service
Extracted CasADi/IPOPT NMPC solver into a dedicated microservice.
- **Port**: `:8002`
- **Dynamic Context**: Fetches bounds and weights from the Governance plane seamlessly.

- **Run Full Stack**: `make stage1-gateway`
- **Smoke Tests**: `make stage1-smoke` and `make stage1-opt-smoke`
- **Demo Note**: The `demo.py` and Streamlit UI now point to the Gateway (`API_BASE` -> Gateway) while keeping all endpoint paths intact.

## 🛠️ Tech Stack
- **Optimizer**: Python, CasADi (IPOPT), NumPy, SciPy
- **Backend**: FastAPI, Pydantic, OTel
- **Frontend**: Streamlit, Matplotlib
- **Reporting**: FPDF2
- **Data**: JSON-backed deterministic storage with FileLocking

## ✅ Validation & Testing
Run all tests including Phase 5:
```bash
make test
```
