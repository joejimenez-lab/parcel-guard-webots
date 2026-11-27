"""Independent fixture and simulated alert endpoint; never classifies events."""
import json
import os
from pathlib import Path
import sqlite3
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lockbox.alert_receiver import AlertReceiver
from controller import Supervisor

robot = Supervisor()
dt = int(robot.getBasicTimeStep())
scene_rx = robot.getDevice('scene_rx')
event_rx = robot.getDevice('event_rx')
tx = robot.getDevice('fixture_tx')
for receiver in (scene_rx, event_rx):
    receiver.enable(dt)
parcel = robot.getFromDef('PARCEL')
door = robot.getFromDef('DOOR')
translation = parcel.getField('translation')
root = Path(__file__).resolve().parents[2]
default_receipts = str(root / '.runtime/alert-receipts.sqlite3') if Path(robot.getWorldPath()).name == 'delivery_box.wbt' else ''
receipt_path = os.environ.get('PARCEL_GUARD_RECEIVER_PATH', default_receipts)
endpoint = None
instance = uuid.uuid4().hex
duplicates = 0
drop_acks = dropped_acks = 0
storage_fault = False
animation = None

def send(action, **data):
    tx.send(json.dumps({'action': action, **data}).encode())

frame = 0
while robot.step(dt) != -1:
    frame += 1
    while scene_rx.getQueueLength():
        try:
            command = json.loads(scene_rx.getString())
            action = command.get('action')
            if action in ('parcel_in', 'parcel_out'):
                target = [0, 0, .32] if action == 'parcel_in' else [1.05, -.35, .10]
                if command.get('animate'):
                    # Approach the open front at the centre of the doorway.
                    # A direct diagonal from the staging position crosses a side wall.
                    outside = [0, -.60, .38]
                    waypoints = ([translation.getSFVec3f(), [1.05, -.60, .38], outside, target]
                                 if action == 'parcel_in' else
                                 [translation.getSFVec3f(), outside, [1.05, -.60, .38], target])
                    animation = (robot.getTime(), waypoints)
                else:
                    translation.setSFVec3f(target)
            elif action == 'impact':
                door.addForce([0, -float(command.get('force', 75)), 0], bool(command.get('local', False)))
            elif action == 'force_open':
                send('actuator_override', open=True)
            elif action in ('jam_latch', 'release_latch'):
                send('actuator_jam', jammed=action == 'jam_latch')
            elif action in ('jam_door', 'release_door'):
                send('door_jam', jammed=action == 'jam_door')
            elif action == 'drop_acks':
                drop_acks = int(command.get('count', 3))
            elif action == 'restart_controller':
                robot.getFromDef('BOX').restartController()
            elif action == 'sensor_fault':
                send('sensor_override', mode=command.get('mode', 'range'))
            elif action == 'sensor_restore':
                send('sensor_override', mode=None)
            elif action == 'reset':
                robot.simulationReset()
        except (ValueError, TypeError, AttributeError):
            pass
        scene_rx.nextPacket()
    if animation:
        start, waypoints = animation
        progress = min(3, (robot.getTime() - start) / .64)
        segment = min(2, int(progress))
        t = min(1, progress - segment)
        source, target = waypoints[segment:segment+2]
        ease = t*t*(3-2*t)
        position = [a+(b-a)*ease for a,b in zip(source, target)]
        translation.setSFVec3f(position)
        if progress == 3:
            animation = None
    if endpoint is None and (frame % 6 == 0 or event_rx.getQueueLength()):
        try:
            endpoint = AlertReceiver(receipt_path)
            storage_fault = False
        except (OSError, sqlite3.Error):
            storage_fault = True
    while event_rx.getQueueLength():
        try:
            if endpoint is not None:
                event = json.loads(event_rx.getString())
                duplicates += not endpoint.record(event)
                storage_fault = False
                if drop_acks > 0:
                    drop_acks -= 1
                    dropped_acks += 1
                else:
                    send('ack', session=event['session'], id=event['id'])
        except (ValueError, TypeError):
            pass
        except sqlite3.Error:
            # Keep the event pending at the sender until a write succeeds.
            storage_fault = True
        finally:
            event_rx.nextPacket()
    if frame % 6 == 0:
        sessions = {}
        if endpoint is not None:
            try:
                sessions = endpoint.sessions()
            except sqlite3.Error:
                storage_fault = True
        send('endpoint_status', sessions=sessions, duplicates=duplicates,
             instance=instance, dropped_acks=dropped_acks, storage_fault=storage_fault)

if endpoint is not None:
    endpoint.close()
