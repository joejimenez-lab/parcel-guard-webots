# Parcel Guard Layered Security Demo

Use `worlds/delivery_box.wbt` in Webots R2025a at **real-time speed** and open the Robot Window. The interactive world defaults to layered security; fixed 2468/1357 codes no longer unlock it. The owner console is above the door-entry controls.

## Before class

Use the local demo owner password **owner-5650** unless changed at first initialization with `PARCEL_GUARD_OWNER_PASSWORD`. Just enter the password in the owner console. No separate terminal, authenticator or timed code is needed.

Owner sessions last 300 simulated seconds. Keep Webots at real-time speed for the class demonstration. You can sign in again immediately with the same password, including after a controller restart or a tamper incident. Saved checkpoints retain the existing password verifier, codes and incident state.

## Opening

"Our first version used two fixed demo codes and needed a reset for another delivery. This version lets the owner authorize each delivery, revoke access, and recover from a security incident using the owner password."

## Four to six minute sequence

1. **Verify the owner.** Enter the owner password. The owner verification countdown appears; no owner-session token is displayed.
2. **Issue and revoke a code.** Create a courier code with a five-minute lifetime. It appears once. Copy it, click **Revoke** next to that credential, and try it under Request access with Courier selected. The box must deny it and stay secured.
3. **Complete an authorized cycle.** Create another courier code, enter it at the door, and unlock. Expand Test controls, place the parcel, then close and secure. Show the delivery event only after closure and bolt confirmation. Create an Owner collection code and use it to retrieve the parcel. Another courier code can start the next delivery in the same policy session; no reset is required.
4. **Trigger an incident.** Create an unused code, then click the ordinary **Impact** control while the box is secured. The banner changes to Security lockdown, all issued codes are revoked, and the owner session ends. The physical secured status remains distinct from the administrative access block. Try the previously valid code: it must be rejected.
5. **Show persistence and recover.** Click **Restart controller** and show that lockdown remains. Sign in again with the owner password, and click **Clear lockdown** after the door and bolt confirm secured. The old code is still revoked. Issue a new code to resume service.

If running short, omit the collection portion of step 3 and use the recorded evaluation results for the second delivery. Explain that the full automated security scenario verifies two deliveries, collection, expiration, revocation, restart and recovery.

## Questions to be ready for

- **Who manages access?** Only a signed-in owner can issue or revoke codes. A courier delivery code cannot manage credentials. The local password verifier and test controls model a trusted demo host, not a production network boundary.
- **Can reset bypass lockdown?** No. In security mode, New session is denied, and a controller/world restart reloads the persistent incident. Owner sessions are not restored.
- **Does clearing lockdown restore old codes?** No. They remain revoked. The verified owner must issue a fresh code.
- **Why does the box say physically secured during lockdown?** Door and bolt feedback confirm physical closure. Lockdown independently blocks new access until owner review.
- **What if there is a sensor/bolt fault?** Clear lockdown stays disabled until measured physical security returns. A security action never overrides an unresolved actuator or sensor fault.

## Verification commands

`python3 scripts/verify_progress2.py` checks saved code/evidence hashes without Webots. To rerun the suite, install Webots R2025a, Python 3.10+ and the demo-studio Node dependencies, then run `python3 scripts/run_all.py`. The old numerical acceptance worlds use legacy fixture codes for comparison; `delivery_box_security.wbt` separately tests the default owner workflow. The evaluation uses an isolated test owner password; interactive state and credentials remain separate.
