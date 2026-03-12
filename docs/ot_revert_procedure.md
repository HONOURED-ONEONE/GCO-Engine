# OT Revert Procedure

The `revert` procedure is a critical safety feature that ensures the plant is restored to a safe state in the event of an automated control failure.

## 1. Automatic Revert
- Triggered automatically by the OT service when a read-back check fails.
- Reverts the plant to the `last_good_setpoint` that was previously verified.
- The system will immediately notify the operator of the failure.

## 2. Manual Rollback
- Can be triggered manually by an Admin or Engineer if they observe unexpected plant behavior.
- Uses the `POST /ot/rollback` endpoint to revert to the `last_good_setpoint`.

## 3. Revert Verification
- The OT service will verify that the revert write was successful.
- Failure to revert will result in a critical alarm and an audit log entry.

## 4. Troubleshooting
- In the event of a persistent failure to revert, operators must:
  - Use the plant's local HMI/SCADA system for manual control.
  - Activate the plant's physical emergency stop if safety is compromised.
  - Review the OT service logs and configuration.
- The system will be automatically disarmed until the issue is resolved.
