# OT Commissioning Checklist

Before enabling `guarded` mode or performing live writes, the following commissioning steps must be completed and verified.

## 1. Physical Connectivity
- [ ] Network connectivity to the OPC-UA server is established.
- [ ] Ping/latency to the server is within acceptable limits (< 100ms).

## 2. Configuration & Tag Mapping
- [ ] `OTConfig` endpoint URL is correct.
- [ ] Authentication credentials (if used) are valid.
- [ ] All tags in the `tag_map` (shadow, live, alarms) are correctly mapped to OPC-UA nodes.
- [ ] Tags are readable and writable (as appropriate) by the OT service.

## 3. Safety & Interlocks
- [ ] Alarm nodes are correctly identified.
- [ ] `alarm_blocklist` is populated with critical alarms that should block writes.
- [ ] `min_write_interval_sec` is set to a safe value for the plant.
- [ ] `readback_tolerance` is calibrated for the plant's sensors.

## 4. Verification
- [ ] `POST /ot/commissioning/verify` returns a successful readiness report.
- [ ] Shadow writes have been performed and verified for at least 24 hours.
- [ ] Manual revert procedure has been tested and verified.

## 5. Final Approval
- [ ] Operator lead approval received.
- [ ] Engineer lead approval received.
- [ ] Maintenance lead approval received.
