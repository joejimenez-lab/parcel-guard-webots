# Parcel Guard User Guide

## Current interactive workflow

Open `worlds/delivery_box.wbt` in Webots R2025a, select real-time speed and open its Robot Window. The interactive controller enables layered security and local checkpoints by default. The owner security console appears above the door-entry controls.

1. Enter the local demo owner password **owner-5650** in the owner console and sign in. No authenticator, second device or timed code is needed.
2. Create a courier code and choose its lifetime. Copy the generated eight-digit value; it is returned once and is absent from event exports. Select Courier under Request access, enter the code and unlock.
3. Wait for the door to open, then use Test controls to place the parcel. Close and secure. Delivery is recorded after measured door closure and bolt locking.
4. Create an Owner collection code, select Owner under Request access and use it to retrieve the parcel. Create a new courier code for another delivery; a policy reset is unnecessary.
5. Revoke an unused code from its credential row when access should be cancelled. Codes also stop working after one use or expiry.

Owner sessions last five simulated minutes. You can sign in again immediately using the same password; a new sign-in invalidates the old session. Five incorrect passwords trigger a 60-simulated-second pause. `PARCEL_GUARD_OWNER_PASSWORD` can configure the password at first initialization; saved state retains its verifier. Existing checkpoints upgrade automatically without resetting issued codes or incidents.

## Security incidents

An unexplained impact, opening or parcel movement triggers lockdown. All issued codes are revoked, the current owner session ends, and active access is cancelled. The controller attempts closure and locks only after measured feedback permits it. A physically secured box can still be in administrative lockdown.

To recover, sign in with the owner password again, then clear lockdown after physical security is confirmed. Old credentials remain revoked. Issue a fresh access code afterward. New session cannot clear a security incident, and controller/world restart retains lockdown.

## Recovery and fault controls

- **Restart controller** reloads saved events, credential state and any lockdown. It cancels active access, discards owner sessions and closes before locking. The control is enabled when the panel shows Saved locally.
- **Impact** creates an ordinary unapproved disturbance. In security mode it can trigger incident lockdown. **Strong impact** is intended to demonstrate detection during approved open-door access; it applies a stronger force relative to the door.
- **Invalid sensor** injects an impossible distance. Access is disabled until Restore sensor supplies three stable valid readings. Unresolved faults prevent lockdown clearance.
- **Disconnect link / Restore link** demonstrate the durable sender queue. Events remain pending until acknowledged. Receiver deduplication still resides in memory.
- **Block bolt / Release bolt** and **Block door / Release door** demonstrate measured fault detection and recovery.

Local state is stored in `.runtime/lockbox-state.json` with private file permissions. It includes the private credential digest key and password verifier and is not encrypted or protected against malicious host access. Do not share runtime files. The project ZIP excludes them. A damaged/unwritable checkpoint disables access; preserve it when diagnosing the fault.

## Legacy evaluations

The original acceptance worlds use fixed fixture codes, 2468 and 1357, to retain a comparable numerical benchmark. They do not represent the current interactive access policy. The dedicated `delivery_box_security.wbt` uses isolated password-only owner sign-in and managed codes. `python3 scripts/run_all.py` executes both sets and records their separate evidence. Existing videos show the earlier workflow; use `PROGRESS_REPORT_2_DEMO.md` for the current class demonstration.
