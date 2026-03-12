# Resilience & Failure Matrix

This matrix describes the expected behavior of each service in the pure microservices stack during partial dependency failures.

| Unavailable Service | Impacted Service(s) | Observed Behavioral Degradation | Recovery Strategy |
| :--- | :--- | :--- | :--- |
| **Governance** | Optimizer, Gateway, OT | **Fail-Closed**. Optimizer cannot fetch bounds; Gateway denies requests; OT write-blocker prevents updates. | **Critical**. Requires high-availability for production. |
| **KPI** | Policy, Evidence, Twin | **Degraded**. Policy cannot form experiences; Evidence snapshots are incomplete. | Automatic recovery once the KPI ingest stream resumes. |
| **Policy** | Optimizer | **Degraded**. Optimal recommendations are still generated, but counterfactual/policy explanations are missing. | Service resumes providing explanations upon recovery. |
| **Twin** | Evidence, Policy | **Degraded**. No simulation-based validation or counterfactuals. | Use historical data as a fallback for training. |
| **OT** | Gateway, Optimizer | **Partial Fail**. Optimizer still generates proposals, but shadow/guarded writes fail with a 502/504 error. | Re-establish OPC-UA connection. |
| **LLM** | Evidence, Pilot | **Degraded**. No natural language summaries or ROI narratives. Structured data remains available. | Retry logic on non-critical endpoints. |
| **OPA** | Gateway | **Full Fail**. Gateway fails closed if OPA is unreachable to prevent unauthorized access. | Requires high-availability or local policy cache. |
| **Database** | All | **Full Fail** (Write) / **Degraded** (Read). Depends on caching. Services fail closed for any state-modifying operations. | Automatic reconnection; persistent storage cluster required. |

## 🧪 Simulation
Failures are simulated using `scripts/failure_matrix.sh`, which stops target containers and verifies the health of dependent routes.
