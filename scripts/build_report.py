"""Build the evidence summary and CSV exports directly from current JSON reports."""
import csv
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RESULTS=ROOT/'results'
def load(name):return json.loads((RESULTS/f'{name}.json').read_text())
def export(name, rows):
    if not rows:return
    keys=list(dict.fromkeys(k for row in rows for k in row))
    with (RESULTS/f'{name}.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=keys,lineterminator="\n");writer.writeheader()
        writer.writerows({k:json.dumps(v,separators=(',',':')) if isinstance(v,(dict,list)) else v for k,v in row.items()} for row in rows)
s=load('webots_sensor_trials');c=load('webots_classification');d=load('webots_development');b=load('webots_benchmark')['checks'];r=load('robustness')
p2=load('webots_progress2');p2logic=load('progress2_regressions');dashboard=load('dashboard_validation')
security=load('webots_security');security_logic=load('security_layers')
export('parcel_trials',s['trial_details']);export('classification_trials',c['trial_details'])
export('motor_cycles',b['motor_cycles']['trials']);export('latency_trials',b['alert_latency']['details'])
export('outage_trials',b['connection_recovery']['outages']);export('access_trials',b['access_security']['details'])
text=f'''# Parcel Guard evaluation

Generated from simulator outputs. Source/configuration hashes and report hashes are in `evaluation_manifest.json`.

The original numerical acceptance suite uses legacy fixture credentials for comparison. The interactive world defaults to layered security; its password sign-in, managed codes, repeated deliveries and lockdown are evaluated separately in `webots_security.json`.

## Proposal acceptance criteria

| Requirement | Target | Actual | Evidence |
|---|---:|---:|---|
| Balanced parcel presence | ≥48/50 | {s['correct']}/50 | `webots_sensor_trials.json`, `parcel_trials.csv` |
| Balanced 4-class sequences | 15 per class, 60 total | {c['trials']} total | `classification_trials.csv` |
| Macro F1 | ≥0.90 | {c['macro_f1']:.2f} | `webots_classification.json` |
| False tamper alarms | ≤2/45 non-tamper sequences | {c['false_alarms']}/45 | Confusion matrix below |
| Normal actuator cycles | ≥99/100 | {b['motor_cycles']['successful']}/100 | `motor_cycles.csv` |
| Sensor sample → alert queue | ≥29/30 within 1 simulated second | {b['alert_latency']['within_1s']}/30 | `latency_trials.csv` |
| Offline event recovery | 10 outages × 10 events, all once | {b['connection_recovery']['recovered_events']}/100 | `outage_trials.csv` |
| Invalid/expired/used/wrong-role/replay | Zero unauthorized unlocks in 30 cases | {b['access_security']['unauthorized_unlocks']}/30 | `access_trials.csv` |
| Blocked latch | Fault with secured status false | Both lock and unlock directions pass | `webots_benchmark.json` |
| Five wrong codes in five minutes | 60-second cooldown | Pass, including valid code after expiry | `webots_benchmark.json` |

## Classification comparison

Rows are ground truth, columns are predictions. Every final sequence has recorded sensor motion measurements and event IDs.

| Actual / predicted | Benign motion | Delivery | Retrieval | Tamper |
|---|---:|---:|---:|---:|
'''
for label in ('benign_motion','delivery','retrieval','tamper'):
    vals=c['confusion_matrix'][label]
    text+='| '+label.replace('_',' ').title()+' | '+' | '.join(str(vals[x]) for x in ('benign_motion','delivery','retrieval','tamper'))+' |\n'
text+=f'''
Context-aware controller macro F1: **{c['macro_f1']:.2f}**. Measured motion-only baseline: **{c['motion_only_macro_f1']:.2f}**.
The baseline predicts tamper if the recorded acceleration peak exceeds 10.2 m/s² or the recorded door angle varies by >0.05 rad. It has no code or parcel context. Its predictions are computed per trial from measured traces; its confusion matrix is saved in JSON. It is a simple reference baseline, not an optimized competing classifier.

## Reproducibility and sensing

- Webots R2025a, 32 ms physics/device timestep, world random seed 42.
- Separate development set: seed 5650, 60 sequences, macro F1 {d['macro_f1']:.2f}. Final set: seed 20260930, 60 sequences. Parcel set: seed 20260931.
- Frozen parameters in `config/evaluation.json`. The manifest checks that code and parameters do not change during evaluation. These are separate generated scenario sets, not independent real-world data.
- 25 generic distance rays, Gaussian relative standard deviation 0.5%, enter/exit thresholds 0.40/0.43 m, three stable samples. Final trials include boundary placements and dimensions 0.12–0.29 × 0.12–0.25 × 0.10–0.24 m.
- Presence sensitivity {s['sensitivity']:.0%}; specificity {s['specificity']:.0%}. False negatives {s['false_negatives']}/25; false positives {s['false_positives']}/25.
- Initial idle acceleration peak {c['idle_peak_m_s2']:.3f} m/s² (gravity included); impact threshold 13.0 m/s². Gravity is expected in these raw readings. Thresholds are fixed before the reported run.

## Latency interpretation

The local event queue is filled in the same Python iteration as the first sampled impact threshold crossing, so the measured sensor-to-queue delay is 0 simulated seconds in all 30 trials. This is a discrete-time scheduling result, not a claim of zero physical or network latency. Device sampling is 32 ms; dashboard/status publishing is 96 ms. The independent Supervisor observed the alert within {b['alert_latency']['max_stimulus_to_observer_s']:.3f} simulated seconds of sending each stimulus. Network and video rendering delays are excluded from the proposal latency metric.

## Additional failure checks

- Lost ACKs cause retransmission. The independent endpoint deduplicates `(session, event ID)`; its unique receipt list is checked against all expected outage IDs.
- Motor force is disabled for both locking and unlocking fault trials while commanded targets continue to update. The two-second timeout raises a fault. Recovery requires measured bolt feedback.
- A 20-second access window closes the door automatically and confirms re-locking.
- The separate `webots_edge_cases.json` checks an obstructed door, authorization expiry while open, late parcel movement, measured recovery, early cancellation and malformed commands. Physical hinge stops bound rotation when motor torque is disabled.
- Expired-code cases include offline entry. All five attack categories have 6 independent attempts; cooldown cannot hide missing category coverage.
- {len(r['checks'])} targeted logic regressions cover startup, interrupted debounce, non-finite feedback and JSON, exact token expiry, expired grants, door faults, early close, hysteresis, mid-stroke bolts, concurrent access, request IDs, role scope and ACK races.

## Progress Report 2 improvements

- {p2logic['tests_run']} additional Python regressions passed, including abrupt child-process exit, persisted code use/replay/cooldown state, clock epochs, corrupted storage and failed writes.
- {len(p2['checks'])} Webots scenario groups passed: offline restart with ten impacts, reset protection, recovered ACK/retry delivery, restart during access, invalid sensor range, frozen bolt feedback and strong impact during owner access. Details: `webots_progress2.json`.
- {len(dashboard['checks'])} dashboard checks passed. The panel shows saved state and recovery count, explains storage faults, and exposes restart, strong-impact and sensor-fault fixtures.
- Interactive `delivery_box.wbt` uses `.runtime/lockbox-state.json`. Checkpoints use a checksum, flushed file data and atomic replacement. A storage fault disables access. The audit JSONL remains separate.
- Recovery preserves session/event IDs, the unacknowledged outbox, consumed credentials, replay IDs and cooldown. Active access is cancelled and closure is measured before locking. A new world epoch expires old codes. A new session is rejected while events await ACK.
- A separate 35 m/s² acceleration threshold reports strong impacts even during authorized access, closing or settling. A usable accelerometer remains effective when another device is invalid. This fixed simulation threshold needs hardware calibration.
- Finite but impossible distance/joint readings now cause sensor faults. Frozen bolt feedback is detected during commanded motion by the existing timeout; plausible frozen parcel readings remain unresolved.

## Scope and limitations

The interactive owner workflow adds {security_logic['tests_run']} Python security tests and {len(security['checks'])} Webots security groups: secure default, owner password, revocation, delivery/collection, another delivery without reset, expiry, lockdown, restart persistence, fresh owner recovery and redaction. Fixed 2468/1357 codes are disabled in the interactive world. Owner sessions require only the owner password, expire after 300 simulated seconds, and are invalidated by restart or tampering. A tamper event revokes every outstanding code. A new password sign-in and measured closure/locking are required to clear lockdown; reset cannot bypass it. New eight-digit code plaintext is returned privately once; shared status and audit exports contain metadata only. Owner password verifiers use PBKDF2-HMAC-SHA256; issued codes use a keyed digest. Digest keys remain in the local private checkpoint. Owner sessions and delivery-code lifetimes use simulation time. The local UI, fixture and test reply channel are not a secure production transport.

The tests use one parcel and a simulated notification endpoint. Controller decisions use devices; only the separate Supervisor fixture knows scene coordinates. The baseline suite uses demo PINs; the default interactive workflow uses password sign-in and managed one-use codes. Cryptographic primitives do not establish production security: cloud identity, TLS and tamper-resistant local storage are outside this simulation. Interactive local checkpoints and abrupt-process/restart tests now cover sender recovery; actual power interruption was not tested. Receiver deduplication remains in memory, so simultaneous sender/endpoint restart is not an exactly-once guarantee. Pending delivery confirmation is cancelled on restart because uninterrupted custody cannot be inferred. Runtime JSONL is an audit export, not the recovery database. The door/bolt model demonstrates motion and feedback; it is not a forced-entry strength test. Fault detection covers non-finite/range feedback and target timeouts; plausible stuck-at parcel readings remain a limitation. No conclusions about real Wi-Fi, TLS, delivery services, outdoor weather or physical security are claimed. Existing videos and final-paper PDFs describe the earlier version; Progress Report 2 is the current change record.

## Videos

`output/Parcel Guard - Delivery Workflow.mp4` and `output/Parcel Guard - Security Recovery.mp4` combine native Webots footage with the actual browser control page connected to the running controller. `output/raw/` holds the unedited footage. Each recording has scenario assertions and a complete telemetry sidecar in `results/`. The sidecars supply the measured feedback. Interface capture reports retain the button/form command sequence and hashes of both unedited recordings.
'''
(RESULTS/'REPORT.md').write_text(text)
print('Wrote evidence report and six CSV exports')
