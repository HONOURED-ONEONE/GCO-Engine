# Service Failure Behavior

Detailed documentation of individual service responses to failure conditions.

## 🏢 Governance Service
- **Failure**: Service down.
- **Impact**: Critical. All services that rely on bounds validation (Optimizer, OT) will fail-closed.
- **API Response**: Gateway returns `502 Bad Gateway`.

## 📈 KPI Service
- **Failure**: Service down.
- **Impact**: KPI ingest fails. Policy training and Evidence snapshots are degraded.
- **Degraded Mode**: Systems continue with the last known KPI state; new data is buffered if clients support it.

## 🛡️ OT Service
- **Failure**: Connector failure (OPC-UA).
- **Impact**: Write-blocker prevents updates.
- **Detection**: `health` endpoint reports `status: error`.

## 🚪 Gateway (PEP)
- **Failure**: OPA unreachable.
- **Impact**: Full system lockout.
- **Reasoning**: Security priority ensures no request is allowed if authorization cannot be verified.

## 🗄️ Persistence (DB)
- **Failure**: DB connection lost.
- **Impact**: CRUD operations fail.
- **Strategy**: SQLAlchemy handles reconnection; services should retry or return `503 Service Unavailable`.
