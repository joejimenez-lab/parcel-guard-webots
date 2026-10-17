"""End-to-end scripted Webots trial; writes machine-readable evidence."""
import json
from pathlib import Path
from controller import Supervisor

robot = Supervisor()
step_ms = int(robot.getBasicTimeStep())
transmitter = robot.getDevice("command_tx")
receiver = robot.getDevice("status_rx")
receiver.enable(step_ms)


def send(action, **values):
    transmitter.send(json.dumps({"action": action, **values}).encode("utf-8"))


schedule = {
    10: ("access", {"code": "2468", "request_id": "walkthrough-courier"}),
    52: ("parcel_in", {}),
    76: ("close", {}),
    118: ("link_off", {}),
    128: ("impact", {}),
    143: ("link_on", {}),
    172: ("access", {"code": "1357", "request_id": "walkthrough-owner"}),
    214: ("parcel_out", {}),
    238: ("close", {}),
}

last = None
max_accel = 0.0
open_samples = 0
bolt_orientation_error = 0.0
door_node = robot.getFromDef('DOOR')
bolt_node = robot.getFromDef('BOLT')
for frame in range(310):
    if robot.step(step_ms) == -1:
        break
    if frame in schedule:
        action, values = schedule[frame]
        send(action, **values)
    while receiver.getQueueLength():
        last = json.loads(receiver.getString())
        max_accel = max(max_accel, max(abs(value) for value in last.get("door_accel_m_s2", [0])))
        receiver.nextPacket()
    if last and last['door_angle_rad'] > 1.0:
        open_samples += 1
        bolt_orientation_error = max(bolt_orientation_error, max(
            abs(a - b) for a, b in zip(door_node.getOrientation(), bolt_node.getOrientation())))

checks = {}
if last:
    kinds = last["event_kinds"]
    checks = {
        "delivery_recorded": kinds.count("delivery") == 1,
        "retrieval_recorded": kinds.count("retrieval") == 1,
        "impact_alert_recorded": "tamper" in kinds,
        "outage_and_recovery_recorded": "link_lost" in kinds and "link_restored" in kinds,
        "queue_drained": last["pending"] == 0,
        "delivered_exactly_once": len(last["delivered_ids"]) == len(set(last["delivered_ids"])) == len(kinds),
        "final_door_closed": last["door"] == "closed",
        "final_latch_locked": last["latch"] == "locked",
        "final_parcel_empty": last["parcel"] == "empty",
        "bolt_follows_open_door": open_samples >= 5 and bolt_orientation_error < 0.001,
    }
else:
    checks = {"received_status": False}

report = {"passed": all(checks.values()), "checks": checks, "max_door_axis_accel_m_s2": max_accel,
          "open_door_samples": open_samples, "max_bolt_orientation_error": bolt_orientation_error,
          "final_status": last}
path = Path(__file__).resolve().parents[2] / "results" / "webots_smoke.json"
path.parent.mkdir(exist_ok=True)
path.write_text(json.dumps(report, indent=2))
print("WEBOTS_TRIAL", json.dumps({"passed": report["passed"], "checks": checks}), flush=True)
robot.simulationQuit(0 if report["passed"] else 1)
