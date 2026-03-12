# KPI Ingestion Service (Stage-3)

Standalone FastAPI microservice for KPI Ingestion in the GCO Engine.

## Overview

The KPI service is responsible for ingesting, validating, and persistently storing batch KPIs. It enforces idempotency by `batch_id` and runs continuous anomaly detection based on pre-defined configurable rules.

## Endpoints

* `POST /kpi/ingest`: Idempotent upsert of KPI data.
* `GET /kpi/recent?limit=50`: Get the latest N KPIs.
* `GET /kpi/health`: Internal health and metrics.
* `GET /kpi/stats`: Internal rolling stats.

## Anomaly Rules

Anomalies are flagged if any of the following apply:
- **Rule A:** `quality_deviation` is true.
- **Rule B:** `yield_pct` is below `YIELD_MIN` (default 80.0).
- **Rule C:** `energy_kwh` is outside the `[p10, p90]` band of the last 10 batches.

## Idempotency

Upserts are based on `batch_id`. Re-ingesting the same `batch_id` updates existing fields and timestamps without duplicating records.

## Caveat: No Corridor Mutation

The KPI service strictly manages KPI data. It **does not** change corridor state or mutate plant models. It communicates via audit events to the Governance service and optionally notifications to the Policy service.

## Environment Variables

* `GOVERNANCE_BASE`: Governance service URL (default: http://governance:8001).
* `POLICY_NOTIFY_BASE`: Policy service URL for notifications (optional).
* `YIELD_MIN`: Minimum yield percentage to not flag as an anomaly (default: 80.0).
* `ALLOW_ORIGINS`: CORS origins (default: *).
