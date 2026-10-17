# Software requirements

This specification consolidates the supplied proposal and final-assignment requirements for the delivered Webots project. R1–R14 use the same IDs as the final report. Additional review safeguards are identified separately from the original numerical targets.

## Actors and operating environment

The courier deposits a parcel using a temporary credential. The owner collects it using an owner credential. The classroom operator controls a separate scenario fixture. The local endpoint receives events and acknowledges their IDs. Test runners set scenes and hold ground-truth labels; the detector reads virtual sensors only.

The supported evaluation environment is Webots R2025a, Python 3.10+, a 32 ms timestep and one parcel at a time. The controller and test suite use Python's standard library plus the Webots API. Internet access, a physical keypad, a purchased lock and cloud services are not required to run the simulation.

## Required behavior and acceptance

| ID | Requirement | Acceptance evidence |
|---|---|---|
| R1 | Detect empty/occupied state from device readings over varied parcel dimensions and positions | At least 48 correct of 50 balanced Webots presence trials |
| R2 | Distinguish delivery, retrieval, benign motion and suspected tamper using access and sensor context | 15 final sequences per class; macro F1 at least 0.90; confusion matrix and measured motion reference |
| R3 | Limit false tamper alarms in non-tamper sequences | At most 2 false alarms among all 45 non-tamper final sequences |
| R4 | Open only after measured bolt retraction; close before locking; report secured from feedback | At least 99 successful complete cycles of 100 |
| R5 | Insert sensor-derived alerts into a local queue promptly | At least 29 of 30 within one simulated second from the first sampled threshold crossing |
| R6 | Keep local control running offline, retain events, retry, and deduplicate endpoint processing | All 100 expected alert IDs processed once after 10 outages of 10 events each; complete offline delivery/retrieval also passes |
| R7 | Enforce role, token expiry, single use for both role tokens, occupancy and replay rejection | Zero unauthorized unlocks across 30 independent invalid/expired/reused/wrong-role/replay attempts |
| R8 | Detect a bolt that fails to reach its target and recover from measured feedback | Both locking and unlocking fault cases pass; no false secured state |
| R9 | Pause code entry after five failed credential attempts within five simulated minutes | A valid code is blocked during a 60-second cooldown and works after it expires |
| R10 | Provide local code entry, measured status, event history and fixture controls | Robot Window implementation; 14 DOM checks and recorded browser layout review |
| R11 | Support reproducible evaluation with separate development/final scenarios and failure exports | Fixed seeds/configuration; source and report hashes; saved JSON/CSV trials; nonzero exit on failed gates |
| R12 | Deliver the complete simulation, design, paper, presentation and demos | Public source/release, final PDF, editable PPTX with notes, guides, videos and portable ZIP |
| R13 | Record delivery only after approved placement and measured closure/locking | No delivery while open or blocked; exactly one after lock feedback; removal cancels pending delivery |
| R14 | Reset safely and resume local operation | New session revokes access, reissues temporary tokens, and holds the bolt retracted until the open door closes |

## Review safeguards

Access grants end immediately on close, expiry or invalid sensor feedback. A door held open after a close request faults after three seconds while the bolt stays retracted. Sensor startup and gaps require consecutive usable readings. Non-finite values encode as JSON null. Malformed commands do not stop the adapter. Physical hinge stops bound unpowered travel. Tests in `tests/robustness.py` and `controllers/edge_runner/edge_runner.py` exercise these additions.

## Data and interface constraints

Events use a session namespace and monotonic ID. ACK acceptance requires the current session and a pending event ID. Duplicate packets may occur; duplicate endpoint processing must not. PIN values are omitted from event exports. The fixture and its exposed lab controls are part of the trusted simulation environment.

The UI must distinguish parcel detection from completed delivery, show the current secured state, and identify door, bolt and sensor faults separately. Measurements include units and unavailable values remain visible. Keyboard focus and a single-column narrow layout support use at different window sizes.

## Exclusions and limits

The project makes no requirement claim for physical attack resistance, weatherproofing, real radio/network delay, production credential storage, cloud identity, controller-restart persistence or reliable diagnosis of plausible stuck-at readings. The parcel is positioned by a scenario fixture. Hardware handling, motor pinch protection and collision-free courier placement require a separate physical design and evaluation.
