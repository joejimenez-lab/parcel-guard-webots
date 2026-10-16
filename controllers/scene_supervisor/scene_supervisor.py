"""Independent fixture and simulated alert endpoint; never classifies events."""
import json
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
sessions = {}
duplicates = 0
drop_acks = 0
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
                    animation = (robot.getTime(), translation.getSFVec3f(), target)
                else:
                    translation.setSFVec3f(target)
            elif action == 'impact':
                door.addForce([0, -float(command.get('force', 75)), 0], False)
            elif action == 'force_open':
                send('actuator_override', open=True)
            elif action in ('jam_latch', 'release_latch'):
                send('actuator_jam', jammed=action == 'jam_latch')
            elif action == 'drop_acks':
                drop_acks = int(command.get('count', 3))
            elif action == 'reset':
                robot.simulationReset()
        except (ValueError, TypeError, AttributeError):
            pass
        scene_rx.nextPacket()
    if animation:
        start, source, target = animation
        t = min(1, (robot.getTime() - start) / 1.2)
        ease = t*t*(3-2*t)
        position = [a+(b-a)*ease for a,b in zip(source, target)]
        position[2] += .25 * 4*t*(1-t)
        translation.setSFVec3f(position)
        if t == 1:
            animation = None
    while event_rx.getQueueLength():
        event = json.loads(event_rx.getString())
        ids = sessions.setdefault(event['session'], [])
        if event['id'] in ids:
            duplicates += 1
        else:
            ids.append(event['id'])
        if drop_acks:
            drop_acks -= 1
        else:
            send('ack', session=event['session'], id=event['id'])
        event_rx.nextPacket()
    if frame % 6 == 0:
        send('endpoint_status', sessions=sessions, duplicates=duplicates)
