# OT Connector Service

The OT Connector acts as a bridge between the GCO-Engine and the operational technology (OT) layer, specifically via OPC-UA.

## Architecture
- **DMZ Pattern**: Initiates outbound connections to OT endpoints; no inbound traffic from OT is accepted.
- **Interlocks**: Enforces safety constraints for "guarded" writes.
- **Simulator**: Includes an in-memory OPC-UA simulator for development and testing.

## Safety Guarantees (Interlocks)
1. **Arming Window**: Guarded writes only allowed within a time-boxed arming period.
2. **Corridor Bounds**: Setpoints must be within active corridor bounds from Governance.
3. **Alarms**: Blocked if any critical alarms (from blocklist) are active.
4. **Rate Limiting**: Minimum interval between consecutive writes.
5. **Read-back Confirmation**: Verifies the OT system accepted the value within a configured tolerance.
6. **Fail-safe Revert**: Reverts to the last known good setpoint if write or read-back fails.

## Key Endpoints
- `POST /ot/config/set`: Configure endpoint, tags, and safety parameters.
- `POST /ot/arm`: Open the guarded write window.
- `POST /ot/shadow/write`: Write to non-actuating shadow tags (always allowed).
- `POST /ot/guarded/write`: Perform a safety-guarded write to live tags.
- `GET /ot/status`: Current service state, arming status, and last write result.
- `GET /ot/health`: Connectivity and safety metrics.

## Environment Variables
- `FEATURE_SIMULATED_OPCUA`: (true/false) Use internal simulator.
- `FEATURE_GUARDED`: (true/false) Enable guarded write path (default false/shadow-only).
- `GOVERNANCE_BASE`: Base URL for the Governance service.
- `GATEWAY_SYSTEM_TOKEN`: Bearer token for inter-service communication.

## Audit Events
The service posts the following events to Governance:
- `ot_config_set`
- `ot_armed` / `ot_disarmed`
- `ot_shadow_write_attempt` / `ot_shadow_write_ok` / `ot_shadow_write_fail`
- `ot_guarded_write_attempt` / `ot_guarded_write_ok` / `ot_guarded_write_fail`
- `ot_guarded_revert_ok` / `ot_guarded_revert_fail`
