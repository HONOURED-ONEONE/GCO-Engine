# Runtime Endpoint Ownership

This document lists the ownership of public API routes in the pure microservices runtime. All routes are accessed through the **PEP Gateway (port 8000)**.

| Route Prefix | Service Owner | Description |
|--------------|---------------|-------------|
| `/mode/*` | governance | Operating mode management (AUTO/MANUAL/PILOT) |
| `/corridor/*` | governance | Golden Corridor bounds and approval logic |
| `/governance/*`| governance | Audit trails, health checks, and system metadata |
| `/optimize/*` | optimizer | NMPC-based corridor optimization engine |
| `/kpi/*` | kpi | Real-time KPI calculation and monitoring |
| `/policy/*` | policy | Dynamic policy management and notifications |
| `/twin/*` | twin | Digital twin plant simulation and state |
| `/pilot/*` | twin | Pilot run scenarios and soak testing |
| `/evidence/*` | evidence | Evidence gathering and report generation |
| `/ot/*` | ot | Operational Technology (OT) bridge and interlocks |
| `/llm/*` | llm | LLM-assisted advisory and natural language queries |

## Legacy Monolith

The legacy monolith (formerly `app.api`) is retired from the production runtime stack. Any request to routes not listed above will return a `404 Not Found` error.
