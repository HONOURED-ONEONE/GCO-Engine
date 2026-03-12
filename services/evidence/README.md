# GCO Evidence & Reporting Service

The Stage-5 Evidence & Reporting Service is a read-only microservice that gathers cross-service snapshots, renders deterministic PNG charts, compiles PDF reports, and builds a complete zipped Evidence Pack. It automatically posts audit events to the Governance service.

## Key Constraints
- **Read-Only**: The service cannot mutate control-plane or data-plane state. It only reads from Governance, KPI, Optimizer, Policy, Twin, and LLM services.
- **Deterministic**: Matplotlib charts are rendered with a fixed seed (`numpy.random.seed(4269)`) for reproducibility.
- **Audit**: Every significant action (`snapshot`, `capture`, `pack`) generates an audit trail in Governance.

## Endpoints

- `GET /evidence/snapshot`: Assembles a consolidated cross-service snapshot.
- `POST /evidence/capture`: Renders deterministic charts based on the snapshot.
- `POST /evidence/pack`: Builds a PDF report and zips the Evidence Pack.
- `GET /evidence/files`: Lists artifacts generated for a given `run_id`.
- `GET /evidence/health`: Returns service health and metrics.

## Environment Variables
- `GOVERNANCE_BASE` (default: http://governance:8001)
- `KPI_BASE` (default: http://kpi:8005)
- `OPTIMIZER_BASE` (default: http://optimizer:8002)
- `POLICY_BASE` (default: http://policy:8006)
- `TWIN_BASE` (default: http://twin:8007)
- `LLM_BASE` (default: http://llm:8004)
- `EVIDENCE_DIR` (default: ./evidence)

## Roles
- **Operator**: `snapshot`, `files`
- **Engineer / Admin**: `capture`, `pack`, `health`, `snapshot`, `files`
