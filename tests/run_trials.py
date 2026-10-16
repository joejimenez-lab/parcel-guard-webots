"""Repeatable proposal trials for sensor and controller logic."""
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lockbox.core import Lockbox, Sensors
from lockbox.geometry import parcel_present


def classify(trace_kind, variation):
    box = Lockbox()
    t = variation * 0.013
    occupied = trace_kind == "retrieval"
    start = Sensors(parcel_present=occupied)
    box.previous = start
    if trace_kind == "tamper":
        box.tick(t + 1, Sensors(door_open=True, parcel_present=occupied, latch_locked=True))
    else:
        code = "2468" if trace_kind == "delivery" else "1357"
        assert box.request_access(code, t, start, f"trace-{trace_kind}-{variation}")
        box.tick(t + 0.5, Sensors(parcel_present=occupied, latch_locked=False))
        box.tick(t + 1, Sensors(door_open=True, parcel_present=occupied, latch_locked=False))
        changed = trace_kind == "delivery"
        box.tick(t + 1.2, Sensors(door_open=True, parcel_present=changed, latch_locked=False))
        box.tick(t + 2, Sensors(parcel_present=changed, latch_locked=False))
        box.tick(t + 2.6, Sensors(parcel_present=changed, latch_locked=True))
    kinds = [e["kind"] for e in box.history]
    for label in ("tamper", "delivery", "retrieval"):
        if label in kinds:
            return label
    return "benign_motion"


def main():
    rng = random.Random(5650)
    detection = []
    for _ in range(25):
        size = [rng.uniform(.08, .22), rng.uniform(.08, .20), rng.uniform(.07, .18)]
        center = [rng.uniform(-.10, .10), rng.uniform(-.09, .09), rng.uniform(.35, .52)]
        detection.append(parcel_present(center, size) is True)
    for index in range(25):
        size = [rng.uniform(.08, .22), rng.uniform(.08, .20), rng.uniform(.07, .18)]
        center = [rng.uniform(.65, .95), 0, .36] if index < 20 else [0, 0, 1.0]
        detection.append(parcel_present(center, size) is False)

    labels = ["benign_motion", "delivery", "retrieval", "tamper"]
    truth = [label for label in labels for _ in range(15)]
    predictions = [classify(label, i) for i, label in enumerate(truth)]
    motion_only = ["tamper" for _ in truth]  # A door moved in every trace.
    confusion = {actual: {predicted: sum(a == actual and b == predicted for a, b in zip(truth, predictions))
                          for predicted in labels} for actual in labels}
    f1s = {}
    for label in labels:
        tp = sum(a == label and b == label for a, b in zip(truth, predictions))
        fp = sum(a != label and b == label for a, b in zip(truth, predictions))
        fn = sum(a == label and b != label for a, b in zip(truth, predictions))
        f1s[label] = 2 * tp / (2 * tp + fp + fn) if tp else 0
    false_alarms = sum(a != "tamper" and b == "tamper" for a, b in zip(truth, predictions))
    baseline_f1s = []
    for label in labels:
        tp = sum(a == label and b == label for a, b in zip(truth, motion_only))
        fp = sum(a != label and b == label for a, b in zip(truth, motion_only))
        fn = sum(a == label and b != label for a, b in zip(truth, motion_only))
        baseline_f1s.append(2 * tp / (2 * tp + fp + fn) if tp else 0)

    alert_box = Lockbox()
    alert_latencies = []
    for i in range(30):
        at = i * 1.2
        alert_box.tick(at, Sensors(impact=True))
        alert_latencies.append(alert_box.history[-1]["time"] - at)
        alert_box.tick(at + .1, Sensors())

    recovery_ok = []
    recovery_box = Lockbox()
    for outage in range(10):
        start = outage * 20.0
        recovery_box.set_link(False, start)
        for i in range(10):
            recovery_box.tick(start + 1 + i * 1.2, Sensors(impact=True))
            recovery_box.tick(start + 1.1 + i * 1.2, Sensors())
        recovery_ok.append(len(recovery_box.pending) == 11)
        recovery_box.set_link(True, start + 15)
        recovery_ok[-1] &= len(recovery_box.pending) == 0
    delivered_ids = [e["id"] for e in recovery_box.delivered]
    recovery_ok.append(len(delivered_ids) == len(set(delivered_ids)) == len(recovery_box.history))

    access_box = Lockbox()
    denied = [not access_box.request_access("0000", i * 31.0, Sensors(), f"invalid-{i}") for i in range(30)]
    used_box = Lockbox()
    first_use = used_box.request_access("2468", 0, Sensors(), "first-use")
    used_box.tick(1, Sensors(door_open=True, latch_locked=False))
    used_box.tick(2, Sensors())
    reused_rejected = not used_box.request_access("2468", 3, Sensors(), "second-use")
    expiry_box = Lockbox(courier_valid_until=2)
    expired_rejected = not expiry_box.request_access("2468", 3, Sensors(), "expired")
    replay_box = Lockbox()
    replay_first = replay_box.request_access("1357", 0, Sensors(), "request-1")
    replay_rejected = not replay_box.request_access("1357", 1, Sensors(), "request-1")
    lockout_box = Lockbox()
    for i in range(5):
        lockout_box.request_access("wrong", float(i), Sensors(), f"failed-{i}")
    one_minute_pause = lockout_box.locked_until == 64.0 and not lockout_box.request_access(
        "1357", 5, Sensors(), "during-pause")

    fault_box = Lockbox()
    fault_box.request_access("1357", 0, Sensors(), "fault")
    fault_box.tick(2.1, Sensors(latch_locked=True))
    fault_detected = any(e["kind"] == "latch_fault" for e in fault_box.history)

    closed_box = Lockbox()
    closed_box.request_access("2468", 0, Sensors(), "closed")
    closed_box.tick(.5, Sensors(parcel_present=True, latch_locked=False))
    closed_door_movement_flagged = any(e["kind"] == "tamper" for e in closed_box.history)

    report = {
        "parcel_detection": {"correct": sum(detection), "trials": 50, "target": 48},
        "classification": {"macro_f1": sum(f1s.values()) / 4, "per_class_f1": f1s,
                           "confusion_matrix": confusion, "motion_only_macro_f1": sum(baseline_f1s) / 4,
                           "trials": 60, "target": .90},
        "false_alarms": {"count": false_alarms, "non_tamper_trials": 45,
                         "rate": false_alarms / 45, "target_max": .05},
        "alert_generation": {"within_1s": sum(latency < 1 for latency in alert_latencies), "trials": 30, "target": 29},
        "connection_recovery": {"outages": 10, "events_during_outages": 100, "all_recovered_once": all(recovery_ok)},
        "access": {"invalid_requests": 30, "unauthorized_unlocks": 30 - sum(denied),
                   "expired_code_rejected": expired_rejected, "reused_code_rejected": reused_rejected,
                   "replay_rejected": replay_first and replay_rejected, "one_minute_cooldown": one_minute_pause},
        "latch_fault_detected": fault_detected,
        "closed_door_parcel_movement_flagged": closed_door_movement_flagged,
    }
    report["passed"] = (
        sum(detection) >= 48 and report["classification"]["macro_f1"] >= .9
        and report["false_alarms"]["rate"] <= .05
        and report["alert_generation"]["within_1s"] >= 29
        and all(recovery_ok) and all(denied) and first_use and expired_rejected and reused_rejected
        and replay_first and replay_rejected and one_minute_pause
        and fault_detected and closed_door_movement_flagged
    )
    path = ROOT / "results" / "logic_trials.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
