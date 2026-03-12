# OT Alarm Blocklist

The `alarm_blocklist` is a critical safety configuration that prevents automated writes to the plant when any specified alarm is active.

## Default Blocklist

The following alarms are blocked by default:

- `EmergencyStopActive`: Any emergency stop activation.
- `CommunicationFailure`: Loss of connectivity to critical sensors or controllers.
- `SafetyInterlockTripped`: Any safety interlock activation.
- `PowerSupplyFailure`: Critical power supply issues.
- `HighTemperatureAlarm`: Plant-wide high temperature alarm (above safety limits).
- `LowFlowAlarm`: Critical low flow alarm (above safety limits).

## Configuration

The blocklist is configured in `OTConfig` under the `alarm_blocklist` property.

```json
{
  "alarm_blocklist": [
    "EmergencyStopActive",
    "CommunicationFailure",
    "HighTemperatureAlarm"
  ]
}
```

## Maintenance

- The blocklist must be reviewed and updated whenever plant equipment or safety systems are modified.
- Regular testing of alarm triggers and the resulting write-block behavior is mandatory.
