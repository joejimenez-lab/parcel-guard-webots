# Parcel Guard Progress Report 2 Speaker Guide

The editable deck has 19 slides, including two appendix slides for the workflow, and follows the navy-and-cyan style of the first progress presentation. Allow about 10 minutes for the main slides, an optional three-minute live demonstration after slide 9, and questions. These are rehearsal targets, not a confirmed course time limit.

Owner sign-in is password-only. The default local demo password is **owner-5650**, unless changed at initialization. The deck contains current status screenshots. The earlier videos are historical and do not demonstrate this version.

## Slide 1 Parcel Guard

Introduce Parcel Guard as a Webots delivery security box. This progress report focuses on owner-managed temporary codes, incident lockdown and recovery. Owner sign-in uses a password only. Suggested time: 15 seconds. Template artwork and typography follow the previously submitted progress deck.

## Slide 2 Presentation outline

Suggested time: 15 seconds. Explain that the talk covers progress since Report 1, the owner workflow, incident handling, evidence and remaining work.

## Slide 3 Project overview

Suggested time: 30 seconds. Parcel Guard remains a local Webots model with one parcel at a time. The ordinary Robot reads sensors; only test Supervisors manipulate the scene. Photos show the existing simulated enclosure, which the new access policy controls. Source: README.md; DESIGN.md; docs/assets/overview.jpg.

## Slide 4 Progress since Report 1

Suggested time: 45 seconds. These are implemented changes, not planned features. Explain the new owner workflow and the retained reliability work. Existing checkpoints upgrade without losing the queue or credentials. Owner sign-in is password-only. Sources: lockbox/security.py; lockbox/storage.py; lockbox/core.py; results/security_layers.json.

## Slide 5 Owner security console

Suggested time: 35 seconds. Owner sign-in requires only the demo password. A management session lasts 300 simulated seconds and expires on restart or tampering. Newly issued eight-digit codes are returned once. Screenshot is recorded public status from the current Webots security evaluation, with owner signed out. Sources: plugins/robot_windows/lockbox_window/lockbox_window.html; results/webots_security.json; results/dashboard_validation.json.

## Slide 6 Temporary access codes

Suggested time: 40 seconds. This diagram shows an access credential, not an owner session. Issuing and revoking require owner sign-in. Role mismatch does not consume a valid code. Expiry is exact, one use is committed before opening, and revocation stays effective after restart. Sources: lockbox/security.py; tests/security_layers.py; results/webots_security.json.

## Slide 7 Delivery and collection

Suggested time: 30 seconds. Courier access permits placing a parcel; owner collection uses a separately issued code. Delivery is recorded only after measured door closure and bolt locking. These source images show the same Webots model. A second delivery was verified in the same policy session. Sources: docs/assets/open-door.jpg; docs/assets/parcel-inside.jpg; .build/progress-cs5650/assets/workflow-secured.png; results/webots_security.json.

## Slide 8 Incident lockdown

Suggested time: 45 seconds. An unexplained impact, door opening or parcel movement triggers lockdown. This revokes outstanding codes and ends owner sessions. Physical closure and administrative access are separate: a locked box can remain in lockdown. Screenshot is the measured Webots incident state, not an illustration. Sources: lockbox/core.py; lockbox/security.py; results/webots_security.json.

## Slide 9 Restart and owner recovery

Suggested time: 40 seconds, followed by an optional three-minute live demo. Sign in with the owner password, issue/revoke a code, complete a delivery, inject ordinary Impact while secured, restart the controller, sign in again and clear lockdown after measured security returns. If time is limited, show the recorded screenshots and cite the evaluation. Sources: docs/PROGRESS_REPORT_2_DEMO.md; results/webots_security.json; results/webots_progress2.json.

## Slide 10 System architecture

Suggested time: 45 seconds. The ordinary Robot reads devices and applies sensor, access and event rules. Owner management changes policy, not measured truth. A local checkpoint preserves sender state; the simulated endpoint still keeps deduplication only in memory. Only the independent Supervisor injects scene changes and test faults. Sources: DESIGN.md; lockbox/core.py; controllers/lockbox_controller/lockbox_controller.py.

## Slide 11 Security test results

Suggested time: 45 seconds. Counts come from the passing reports. The 29 Python tests include password-only sign-in, exact expiry, role scope, revocation, session invalidation, checkpoint migration and storage failure. The Webots security suite has ten groups with 28 assertions, including two deliveries without reset. Dashboard checks verify the actual page logic, not physical security. Sources: results/security_layers.json; results/dashboard_validation.json; results/webots_security.json.

## Slide 12 Original benchmark results

Suggested time: 35 seconds. Be explicit: these original acceptance worlds retain legacy fixture credentials for comparison. The managed-code workflow is evaluated separately on the previous slide. The perfect classification result describes generated scenario families, not field performance. Sources: results/webots_sensor_trials.json; results/webots_classification.json; results/webots_benchmark.json.

## Slide 13 Recovery and fault tests

Suggested time: 35 seconds. These are the earlier robustness improvements retained in this iteration. The outbox survives controller restart, while active access does not resume automatically. Sensor range checks are not a complete detector for plausible frozen parcel readings. Receiver restart durability remains future work. Sources: results/robustness.json; results/progress2_regressions.json; results/webots_progress2.json.

## Slide 14 Remaining risks

Suggested time: 35 seconds. Keep the distinction between local logic and production security. The local host and test fixture are trusted. Receiver deduplication remains volatile, plausible frozen parcel readings remain unresolved, and the model does not establish physical attack resistance. These are limits, not passing results. Sources: DESIGN.md; results/REPORT.md.

## Slide 15 Next steps

Suggested time: 25 seconds. These items are planned work. Do not describe them as already implemented. First close receiver durability, then independent parcel sensing, then hardware/calibration work. The current submission is the verified local simulation. Source: docs/PROGRESS_REPORT_2.md.

## Slide 16 Team responsibilities

Suggested time: 15 seconds. This is the responsibility allocation from the original written proposal. It is not a measured record of individual contributions to the current implementation. Integration and review are shared. Source: original proposal responsibility table; previous report Table I.

## Slide 17 Questions

Suggested time: 15 seconds plus questions. Close by emphasizing the new visible capability: the owner can authorize and revoke access, while tampering forces a persistent review state. Both the report and slides distinguish simulated evidence from real-world security claims.

## Slide 18 Access and delivery

Use this appendix slide to show how an issued code leads to access. The code must match the role and be valid, unused and unrevoked. The controller also checks request freshness, cooldown, lockdown, feedback and storage health. An accepted request consumes the code and opens a 20-second simulated access window. Only measured closure and locking confirm delivery with the parcel inside.

## Slide 19 Lockdown and recovery

Use this appendix slide to explain why tampering cancels access, revokes codes and ends the owner session. An unsuccessful recovery check keeps administrative lockdown active while faults are resolved and the door and bolt are secured. A fresh owner sign-in and measured security permit clearance. Old codes stay revoked.

## Classroom handoff

Use the editable deck from the chat viewer and export it as a PowerPoint file before class if needed. Keep the slide PDF as an offline playback backup. The report PDF uses the previous cover, contents and two-column paper format. Read `PROGRESS_REPORT_2_DEMO.md` for the exact live steps.
