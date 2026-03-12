# OT Guarded Write Standard Operating Procedure (SOP)

Guarded writes allow for automated control of plant parameters with continuous safety checks. This SOP outlines the process and requirements for using this mode.

## 1. Prerequisites
- [ ] System is in `guarded` mode (`FEATURE_GUARDED=true`).
- [ ] Commissioning checklist is complete and verified.
- [ ] `OTConfig` is correctly set and validated.
- [ ] Operator is logged in with appropriate permissions.

## 2. Process
- **Step 1: Arm the system:**
  - Call `POST /ot/arm` with a specific duration (e.g., 60 seconds).
  - This opens a temporary write window.
- **Step 2: Submit a guarded write:**
  - Call `POST /ot/guarded/write` with the desired setpoints.
  - The system automatically performs the following checks:
    - Armed check (window still open).
    - Rate limit check (minimum interval since last write).
    - Alarms check (no blocking alarms active).
    - Corridor bounds check (setpoints within governance limits).
- **Step 3: Verification & Read-back:**
  - The system performs the write to live nodes.
  - It immediately reads back the setpoints and verifies them against the written values (within tolerance).
- **Step 4: Auto-revert (if needed):**
  - If read-back fails, the system automatically reverts to the `last_good_setpoint`.

## 3. Monitoring
- Operators must monitor the `OT Status` and `Audit Log` for any failures or violations.
- Any unexpected behavior must be immediately reported to the Engineer lead.

## 4. Emergency Procedures
- Use the `Emergency Stop` physical buttons.
- Call `POST /ot/disarm` to immediately close the write window.
- Use the manual rollback procedure if needed.
