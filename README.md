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

## 🛡️ Production Hardening Wave

The system has been upgraded from a pilot runtime to a **production-credible** stack with a focus on durability, security, and operational safety.

### 📦 Key Upgrades

- **Durable Persistence**: Critical services (Governance, KPI, Policy, OT) now default to **database-backed storage** (SQLAlchemy + Alembic).
- **Security Operations**: Support for `SECURITY_MODE=prod` with strict JWT validation and hardened OPA route policies.
- **OT Commissioning**: Enhanced OT service with `COMMISSIONING_MODE`, write-blockers, and a comprehensive `verify` endpoint.
- **Operational Procedures**: Automated backup, restore, and rollback scripts for disaster recovery and safe configuration changes.
- **Resilience Testing**: New soak and failure matrix testing harness to prove stack stability under load and partial failure.

### 🛠️ Operational Commands

- **Persistence Migration**:
  ```bash
  python3 scripts/migrate_json_to_db_governance.py
  # (Repeat for kpi, policy, ot)
  ```
- **Backup & Restore**:
  ```bash
  make backup
  make restore TIMESTAMP=20260312_120000
  ```
- **Rollback**:
  ```bash
  make rollback-governance VERSION=v1
  make rollback-policy POLICY_ID=p-123
  ```
- **Hardening Smoke Test**:
  ```bash
  make prod-hardening-smoke
  ```

### 📄 New Documentation
- [docs/production_gap_closure.md](docs/production_gap_closure.md)
- [docs/security_model.md](docs/security_model.md)
- [docs/ot_commissioning_checklist.md](docs/ot_commissioning_checklist.md)
- [docs/resilience_matrix.md](docs/resilience_matrix.md)

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
