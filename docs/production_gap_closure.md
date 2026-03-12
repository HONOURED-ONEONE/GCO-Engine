# Production Gap Closure Summary

This document summarizes the upgrades implemented during the **Production Hardening Wave** for the Golden Corridor Optimization (GCO) Engine.

## ✅ Gaps Closed

| Domain | Gap (Pilot/Pre-Prod) | Hardening Solution (Production Credible) |
| :--- | :--- | :--- |
| **Durability** | Critical state stored in local JSON files. | Migrated to **DB-backed persistence** (Postgres/SQLite) using SQLAlchemy + Alembic. |
| **Security** | Reliance on dev-mode mock tokens. | Integrated **JWT verification** with environment-driven `SECURITY_MODE=prod`. |
| **Auth Posture** | Wide OPA policies. | Hardened **OPA route-level policies** with strict RBAC for OT, Policy, and Governance. |
| **Disaster Recovery** | Manual file copies for backup. | Automated **backup, restore, and integrity verification** scripts. |
| **OT Safety** | Demo-grade write logic. | Added **Commissioning Mode**, rate-limiting, read-back confirmation, and a `verify` readiness endpoint. |
| **Resilience** | Unknown behavior on service failure. | Implemented **Soak and Failure Matrix** testing to quantify degradation behavior. |

## 🧪 Operational Assumptions

- **Postgres as Default**: Production deployments assume a dedicated Postgres cluster or managed RDS instance.
- **Secrets Management**: Secrets should be injected via environment variables or secret files, not committed to the repository.
- **OPA Bundle Update**: Policies are bundled with the container image; updates require a fresh deployment or a policy sidecar update.
- **Audit Persistence**: All critical actions are audited to the `governance` service audit log.

## 🚧 Intentionally Deferred Gaps

- **Fully Automated Blue-Green Cutover**: While rollback exists, the actual traffic shift remains a manual infrastructure operation.
- **High-Availability (HA) OPC-UA**: The OT service supports a single OPC-UA endpoint; clustering or failover is handled by the underlying OT network.
- **External Identity Provider (IDP)**: While JWT support is present, the project assumes an external IDP (e.g., Keycloak, Azure AD) will be used to issue tokens.
