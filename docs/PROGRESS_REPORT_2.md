# Parcel Guard
## Project Progress Report 2

**Layered security and owner-managed deliveries**

CS 5650 | California State University, Los Angeles

Joshua Guico, Joe Jimenez and Brandon Lopez

November 17, 2026 | Webots R2025a local simulation

### Progress since Report 1

The October report established delivery and collection with fixed role-specific PINs, measured locking, tamper logging, and alert recovery after a simulated link outage. It identified controller restart recovery and sensor faults as follow-up work. The November milestone adds owner-managed access, persistent lockdown, and tests for those failure cases.

| Area | Report 1 (October) | Report 2 (November) |
|---|---|---|
| Owner access | Fixed courier and owner PINs | Owner signs in and issues or revokes one-use codes with a purpose and expiry |
| Repeated deliveries | Reset to reissue demo PINs | Second delivery verified in the same policy session |
| Tamper response | Log suspected tampering | Revoke outstanding codes, end owner sessions and require an owner to clear lockdown |
| Restart recovery | In-memory queue survives link outages | Local checkpoint restores pending alerts and lockdown after controller restart |
| Fault coverage | Non-finite readings and actuator timeouts | Added range checks, frozen bolt trials, and strong-impact cases during approved access |

The original fixture-PIN benchmark met the proposal targets in October and recorded the same results in November. The November security suite separately verified the owner-managed workflow in 10 Webots groups with 28 assertions. The milestone also adds 29 security policy tests and 26 recovery and fault tests. All 38 original policy checks still pass.

<!-- pagebreak -->

# Owner verification and access codes

### Password-only owner management

The owner signs in with a password. No authenticator, second device or timed code is required. An immediate repeat sign-in is allowed and replaces the previous owner session.

A verified owner receives a short management session held only in memory. It ends after 300 simulated seconds, sign-out, a controller restart or a tamper incident. Five failed owner sign-ins pause further attempts for 60 simulated seconds; that throttle survives restart.

Owner-session and access-code lifetimes use simulation time. Existing checkpoints migrate automatically to the password-only format while retaining the password verifier, issued-code digests and incident state.

### Per-delivery authorization

| Property | Enforced behavior |
|---|---|
| Purpose | A code is issued for courier delivery or owner collection |
| Lifetime | Owner chooses 30 to 3600 simulated seconds; expiry boundary is enforced |
| One use | Successful access consumes the code before the door can open |
| Revocation | Owner can cancel a code before use; it cannot be reactivated |
| Repeated operation | Fresh codes support another delivery without a policy reset |

The interactive world rejects the previous 2468/1357 fixture PINs. Issuing or revoking credentials requires an authenticated owner session. A courier code does not acquire owner collection permissions.

### Secret handling

A newly generated eight-digit code is returned once to the requesting owner interface. Shared status and audit events contain credential metadata, not the code, credential digest key, password or bearer session. Stored access codes use keyed digests; the owner password uses PBKDF2-HMAC-SHA256 with a random salt. The local checkpoint still contains the private credential digest key and assumes a trusted host.

<!-- pagebreak -->

# Tamper lockdown and recovery

### Automatic incident response

An unexplained impact, door opening or parcel movement activates lockdown. The controller revokes all issued codes, cancels owner sessions and ends active access. The panel changes to Security lockdown, while door and bolt feedback continue to show whether the enclosure is physically secured.

The controller attempts closure and waits for measured door closure before extending the bolt. A sensor or actuator fault remains visible and prevents the owner from clearing the incident prematurely.

| Attempt during lockdown | Result |
|---|---|
| Previously valid access code | Denied; outstanding codes have been revoked |
| Previous owner session | Rejected; fresh verification is required |
| New session / policy reset | Denied; it cannot erase the incident |
| Controller restart | Lockdown and revocations reload from local state |
| Clear while physically unsecured | Denied until stable closure and locking are measured |

### Owner recovery

1. The owner signs in again with the owner password; no waiting for a timed code is needed.
2. Physical faults or obstructions are resolved; feedback must confirm a closed door and locked bolt.
3. The owner explicitly clears lockdown.
4. Old codes remain revoked. The owner issues a fresh code to resume service.

The Webots security evaluation verified this sequence after an actual box-controller restart. It also verified that a previously valid code remained rejected after clearance and that a newly issued code completed collection.

### Existing protection retained

Local checkpoints preserve the event queue, consumed credentials, replay IDs, cooldown and incident state. Active access and owner sessions never resume automatically. Range faults disable access, frozen bolt feedback during commanded motion triggers a timeout, and strong impacts can still be reported during approved access. The initial Report 2 test kept the simulated endpoint running during sender restart. The follow-up below also restarts the endpoint.

<!-- pagebreak -->

# Validation and results

### Current security workflow

The dedicated `delivery_box_security.wbt` runs the default security policy against actual Webots device feedback. Its isolated test owner key and credentials are separate from the interactive owner's generated key.

| Scenario group | Verified outcome |
|---|---|
| Secure default and owner sign-in | Fixed PINs rejected; password-only sign-in and immediate repeat sign-in work |
| Revocation and expiration | Cancelled and expired codes could not grant access |
| Managed delivery and collection | Package delivery confirmed after locking; collection completed |
| Another delivery | Second delivery completed in the same policy session |
| Incident and restart | All codes revoked, owner session cancelled and lockdown persisted |
| Owner recovery | Password sign-in cleared a secured incident; old codes stayed revoked |
| Public-status redaction | Password, issued codes and session tokens absent |

**Security evidence:** 29 Python tests, including saved-state migration; 10 Webots groups with 28 assertions; 33 dashboard checks. The prior 26 recovery/fault tests and 38 original policy checks also pass.

### Original numerical benchmark

The original acceptance worlds retain legacy fixture credentials for comparison. They do not establish the classification score of the entire managed-code workflow; the security scenario suite above supplies that workflow's evidence.

| Benchmark | Result in both reports |
|---|---|
| Package presence | 50/50 correct |
| Four-class classification | Macro F1 1.00; 0/45 false tamper alarms |
| Door/bolt cycles | 100/100 completed |
| Unauthorized attempts | 0/30 unlocks |
| Offline impact events | 100/100 recovered |

The full-run manifest binds 50 source/configuration files to 15 passing report files and confirms source stayed unchanged during evaluation. New records are `results/security_layers.json` and `results/webots_security.json`. These are generated simulation scenarios, not field-security trials.

<!-- pagebreak -->

# Follow-up after Progress Report 2

The simulated receiver now stores each alert in SQLite before it returns an acknowledgment (ACK). The pair of session ID and event ID identifies the record. A retry returns an ACK for the existing record.

In Webots, the receiver stored a tamper alert and the fixture dropped its ACK. The link stayed paused while the box and receiver controllers restarted. The box restored the pending alert and the receiver reloaded its receipt. When the link resumed, the box sent the same alert again. The receiver retained **one stored tamper alert** and the sender cleared its queue. See `results/webots_alert_recovery.json`.

# Demonstration and next steps

### Four to six minute demonstration

Open `worlds/delivery_box.wbt`, choose real-time speed and open its Robot Window. The local demo owner password is **owner-5650** unless configured differently at first initialization.

| Step | Demonstration | Visible result |
|---|---|---|
| 1 | Sign in with the owner password | Owner management session becomes active |
| 2 | Create a courier code, revoke it and try it | Revoked credential rejected |
| 3 | Issue fresh codes for delivery and collection | Normal handling completes without resetting |
| 4 | Create an unused code, then inject ordinary Impact | Red lockdown banner; codes revoked; owner signed out |
| 5 | Restart controller, reverify owner and clear | Incident survives restart; fresh authorization restores service |

The rehearsal script is `docs/PROGRESS_REPORT_2_DEMO.md`. The panel can be previewed in the recorded desktop/mobile screenshots under `output/progress2/`. Existing videos show the earlier workflow and are not footage of these additions.

### Next development priorities

Test recovery from power interruption during a receipt write. Add an independent sensing strategy for plausible frozen parcel readings. Replace the trusted local fixture and file assumptions with an authenticated operational interface before any networked or physical deployment. Calibrate impact thresholds using real handling traces.

The current model does not establish resistance to physical forced entry, safe human handling, weather or network attacks. Local host access can expose private state or alter the simulation. Encrypted transport, protected secret storage, and recovery after loss of a storage file remain unverified. A checkpoint and cryptographic primitives alone do not establish production security.

### Reproduction

Run `python3 scripts/verify_progress2.py` to verify saved evidence. With Webots R2025a, Python 3.10+ and the demo-studio Node dependencies installed, run `python3 scripts/run_all.py` to repeat both the legacy benchmark and separate security evaluation.
