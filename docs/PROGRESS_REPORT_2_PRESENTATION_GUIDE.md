# Parcel Guard Progress Report 2 Speaker Guide

The editable deck has 20 slides, including two appendix slides for the workflow, and follows the navy-and-cyan style of the first progress presentation. Allow about 10 minutes for the main slides, an optional three-minute live demonstration after slide 10, and questions. These are rehearsal targets, not a confirmed course time limit.

Owner sign-in is password-only. The default local demo password is **owner-5650**, unless changed at initialization. The deck contains current status screenshots. The earlier videos are historical and do not demonstrate this version.

## Slide 1 Parcel Guard

Introduce Parcel Guard as a Webots delivery security box. This progress report focuses on owner-managed temporary codes, incident lockdown and recovery. Owner sign-in uses a password only. Suggested time: 15 seconds. Template artwork and typography follow the previously submitted progress deck.

## Slide 2 Presentation outline

Suggested time: 15 seconds. Introduce the Report 1 comparison, then point to slide 5 for the receiver restart result.

## Slide 3 Project overview

Suggested time: 30 seconds. Parcel Guard remains a local Webots model with one parcel at a time. The ordinary Robot reads sensors; only test Supervisors manipulate the scene. Photos show the existing simulated enclosure, which the new access policy controls. Source: README.md; DESIGN.md; docs/assets/overview.jpg.

## Slide 4 Progress since Report 1

Suggested time is 45 seconds. Open with what Report 1 had already demonstrated, including delivery and collection, measured locking, tamper logging and offline alert retry. Walk through what changed in November. The owner now issues and revokes one-use codes, a second delivery works without reset, and tampering triggers persistent lockdown. The local checkpoint also restores pending alerts after restart. Evidence is in Report 1, Sections V and VII, and in `results/webots_security.json` and `results/webots_progress2.json`.

## Slide 5 Progress since Report 2

Suggested time is 45 seconds. The box already saved pending alerts in Report 2. The receiver now saves each alert before sending its ACK. In the Webots test, a tamper alert reached the receiver and the ACK was dropped. Both controllers restarted while the link was paused. When the link resumed, the box retried the same ID. The receiver recognized it, kept one alert in storage, and sent the ACK that cleared the box's queue. See `results/webots_alert_recovery.json` for the checkpoints before restart, after restart and after retry.

## Slide 6 Owner security console

Suggested time: 35 seconds. Owner sign-in requires only the demo password. A management session lasts 300 simulated seconds and expires on restart or tampering. Newly issued eight-digit codes are returned once. Screenshot is recorded public status from the current Webots security evaluation, with owner signed out. Sources: plugins/robot_windows/lockbox_window/lockbox_window.html; results/webots_security.json; results/dashboard_validation.json.

## Slide 7 Temporary access codes

Suggested time: 40 seconds. This diagram shows an access credential, not an owner session. Issuing and revoking require owner sign-in. Role mismatch does not consume a valid code. Expiry is exact, one use is committed before opening, and revocation stays effective after restart. Sources: lockbox/security.py; tests/security_layers.py; results/webots_security.json.

## Slide 8 Delivery and collection

Suggested time: 30 seconds. Courier access permits placing a parcel; owner collection uses a separately issued code. Delivery is recorded only after measured door closure and bolt locking. These source images show the same Webots model. A second delivery was verified in the same policy session. Sources: docs/assets/open-door.jpg; docs/assets/parcel-inside.jpg; .build/progress-cs5650/assets/workflow-secured.png; results/webots_security.json.

## Slide 9 Incident lockdown

Suggested time: 45 seconds. An unexplained impact, door opening or parcel movement triggers lockdown. This revokes outstanding codes and ends owner sessions. Physical closure and administrative access are separate: a locked box can remain in lockdown. Screenshot is the measured Webots incident state, not an illustration. Sources: lockbox/core.py; lockbox/security.py; results/webots_security.json.

## Slide 10 Restart and owner recovery

Suggested time: 40 seconds, followed by an optional three-minute live demo. Sign in with the owner password, issue/revoke a code, complete a delivery, inject ordinary Impact while secured, restart the controller, sign in again and clear lockdown after measured security returns. If time is limited, show the recorded screenshots and cite the evaluation. Sources: docs/PROGRESS_REPORT_2_DEMO.md; results/webots_security.json; results/webots_progress2.json.

## Slide 11 System architecture

Suggested time: 45 seconds. The ordinary Robot reads devices and applies sensor, access and event rules. Owner management changes policy, not measured truth. A local checkpoint preserves pending alerts. The separate receiver saves by session and event ID in SQLite before it sends an ACK. Only the independent Supervisor injects scene changes and test faults. Sources: DESIGN.md; lockbox/core.py; controllers/lockbox_controller/lockbox_controller.py.

## Slide 12 Security test results

Suggested time: 45 seconds. Counts come from the passing reports. The 29 Python tests include password-only sign-in, exact expiry, role scope, revocation, session invalidation, checkpoint migration and storage failure. The Webots security suite has ten groups with 28 assertions, including two deliveries without reset. Dashboard checks verify the actual page logic, not physical security. Sources: results/security_layers.json; results/dashboard_validation.json; results/webots_security.json.

## Slide 13 Benchmark results held steady

Suggested time is 35 seconds. Report 1 already met the proposal targets. The November rerun reproduced the benchmark results with the same fixture PINs. Slide 12 gives the separate test results for the owner-managed workflow. See `results/progress1_baseline/REPORT.md` and `results/REPORT.md`.

## Slide 14 Recovery and fault coverage added

Suggested time is 35 seconds. Report 1 identified restart recovery and sensor faults as follow-up work. Report 2 verifies ten queued events surviving a Webots controller restart. Restart discards active grants and owner sessions. The added tests cover invalid sensor ranges, frozen bolt feedback during commanded motion, and injected storage failure. Plausible frozen parcel readings remain open. Slide 5 covers the separate test in which both controllers restart. See `results/progress2_regressions.json` and `results/webots_progress2.json`.

## Slide 15 Remaining risks

Suggested time is 35 seconds. Slide 5 demonstrates process restarts with both local stores intact. Power interruption and storage loss need separate tests. The model still has plausible frozen parcel readings and uses a trusted local host. See `DESIGN.md` and `results/REPORT.md`.

## Slide 16 Next steps

Suggested time is 25 seconds. The dual-controller restart case is complete. Follow-up work covers interrupted receipt writes, independent parcel sensing, and hardware calibration. See `docs/PROGRESS_REPORT_2.md`.

## Slide 17 Team responsibilities

Suggested time: 15 seconds. This is the responsibility allocation from the original written proposal. It is not a measured record of individual contributions to the current implementation. Integration and review are shared. Source: original proposal responsibility table; previous report Table I.

## Slide 18 Questions

Suggested time is 15 seconds plus questions. Close with the two outcomes from the project. The box enforces lockdown after a restart, and the simulated receiver keeps one tamper alert after the ACK is dropped and both controllers restart.

## Slide 19 Access and delivery

Use this appendix slide to show how an issued code leads to access. The code must match the role and be valid, unused and unrevoked. The controller also checks request freshness, cooldown, lockdown, feedback and storage health. An accepted request consumes the code and opens a 20-second simulated access window. Only measured closure and locking confirm delivery with the parcel inside.

## Slide 20 Lockdown and recovery

Use this appendix slide to explain why tampering cancels access, revokes codes and ends the owner session. An unsuccessful recovery check keeps administrative lockdown active while faults are resolved and the door and bolt are secured. A fresh owner sign-in and measured security permit clearance. Old codes stay revoked.

## Classroom handoff

Use the editable deck from the chat viewer and export it as a PowerPoint file before class if needed. Keep the slide PDF as an offline playback backup. The report PDF uses the previous cover, contents and two-column paper format. Read `PROGRESS_REPORT_2_DEMO.md` for the exact live steps.
