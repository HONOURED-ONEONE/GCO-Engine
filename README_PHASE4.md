# GCO Engine - Phase 4: Scale & Harden

Phase 4 evolves the MVP into a production-grade optimization platform.

## Key Features

1.  **NMPC Stack**: 
    - Real-time Nonlinear Model Predictive Control (NMPC) using CasADi/IPOPT.
    - Nonlinear dynamic process model with MHE/Observer for state estimation.
    - Safety fallbacks to heuristic nudges on solver timeout or convergence failure.
    
2.  **OT Integration (Guarded Write-back)**:
    - Dedicated `ot_connector` service with Shadow and Guarded modes.
    - Guarded write-back requires Operator arming and satisfies interlock conditions.
    - Automatic disarming and audit trails for all PLC/SCADA interactions.

3.  **Production MARL Coach**:
    - Experience Store for trajectory logging and counterfactual evaluation.
    - Policy Registry for versioned RL policies (offline training simulation).
    - Policy lifecycle management (Train -> Evaluate -> Activate).

4.  **Enterprise Security & Governance**:
    - JWT-based Role-Based Access Control (RBAC): Operator, Engineer, Admin, Auditor.
    - Tamper-evident Audit Logging with chained SHA-256 hashes for immutability.
    - Secrets management and OIDC-ready authentication flow.

5.  **SRE-Level Observability**:
    - SLO/SLI tracking for optimizer latency (p95 <= 250ms) and solver success rates.
    - Health endpoints integrated with Prometheus/Grafana.
    - Structured logging with trace correlation.

## Local Deployment

### Using Docker Compose
```bash
docker-compose up --build
```

- API: `http://localhost:8000`
- Frontend: `http://localhost:8501`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`

## Using New Features (Frontend)

1.  **Login**: Use the sidebar select box to switch between roles (`op_01`, `eng_01`, `admin_01`).
2.  **OT Control**: In the sidebar, arm the OT connector for a specific duration to enable write-back.
3.  **Optimizer**: Go to the "Optimizer Console" tab. Enable "OT Write-back" checkbox and run recommendation.
4.  **Policy Management**: In "Policy Registry" tab, trigger training or activate different RL policies (Admin only).
5.  **Audit**: In "Governance Audit" tab, view the chained logs and verify integrity.

## Testing
Run all tests including Phase 4:
```bash
python3 -m pytest tests/
```
