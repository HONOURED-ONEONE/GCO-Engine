# Golden Corridor Optimization Engine (Track B)

Phase 5: Judge Demo Automation & Evidence Pack

## 🚀 Final Cut-Over: Pure Microservices Stack (Phase 7+)

The Golden Corridor Optimization (GCO) Engine has completed its transition to a pure microservices runtime. The legacy monolith is retired from the production stack.

### Quickstart (Pure Service Stack)

1.  **Install Dependencies**:
    ```bash
    make install
    ```

2.  **Start Pure Stack**:
    ```bash
    make cutover-up
    ```
    *(Starts Gateway, Governance, Optimizer, KPI, Policy, Twin, Evidence, OT, LLM, and OPA)*

3.  **Verify Migration**:
    ```bash
    make cutover-smoke
    ```

4.  **Start UI**:
    ```bash
    make ui
    ```
    *(Open http://localhost:8501)*

5.  **Run Full Automated Demo**:
    ```bash
    make judge-demo
    ```

### 📦 Key Capabilities

- **Unified Gateway (PEP)**: The `gateway` (port 8000) is the sole entrypoint, enforcing Zero-Trust via OPA.
- **Extracted Microservices**: Every functional domain (Mode, Corridor, Optimize, KPI, Policy, Twin, Evidence, OT, LLM) is now a dedicated service.
- **Legacy Retirement**: The monolith (`app/api/`) remains in the repo as a migration artifact only.

## 🛡️ Runtime Endpoint Ownership
Refer to [docs/runtime_ownership.md](docs/runtime_ownership.md) for a full mapping of route prefixes to service owners.

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
