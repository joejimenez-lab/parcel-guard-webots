"""Device adapter. This Robot has no Supervisor/scene-coordinate privileges."""
import json
import os
import uuid
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lockbox.core import Lockbox
from lockbox.sensing import SensorFilter, CONFIG
from lockbox.protocol import encode_status
from controller import Robot

robot = Robot()
step_ms = int(robot.getBasicTimeStep())
door_motor = robot.getDevice('door_motor')
latch_motor = robot.getDevice('latch_motor')
latch_brake = robot.getDevice('latch_brake')
door_position = robot.getDevice('door_position')
latch_position = robot.getDevice('latch_position')
door_accel = robot.getDevice('door_accel')
receiver = robot.getDevice('command_rx')
emitter = robot.getDevice('status_tx')
scene_tx = robot.getDevice('scene_tx')
event_tx = robot.getDevice('event_tx')
security_reply_tx = robot.getDevice('security_reply_tx')
led = robot.getDevice('status_led')
for device in (door_position, latch_position, door_accel, receiver):
    device.enable(step_ms)
parcel_sensors = [robot.getDevice(f'parcel_{ix}_{iy}') for ix in range(CONFIG['sensor_grid']) for iy in range(CONFIG['sensor_grid'])]
for sensor in parcel_sensors:
    sensor.enable(step_ms)
root = Path(__file__).resolve().parents[2]
# Only the interactive world saves across launches by default. Evaluation worlds
# use isolated stores explicitly, so one trial cannot inherit another's codes.
default_state = str(root / '.runtime/lockbox-state.json') if Path(robot.getWorldPath()).name == 'delivery_box.wbt' else ''
state_path = os.environ.get('PARCEL_GUARD_STATE_PATH', default_state) or None
secure_mode = os.environ.get('PARCEL_GUARD_SECURE_MODE', '1' if Path(robot.getWorldPath()).name in ('delivery_box.wbt', 'delivery_box_security.wbt') else '0') == '1'
clock_epoch = robot.getCustomData() or uuid.uuid4().hex
robot.setCustomData(clock_epoch)
logic = Lockbox(auto_ack=False, start_time=robot.getTime(), state_path=state_path, clock_epoch=clock_epoch,
                secure_mode=secure_mode, owner_password=os.environ.get('PARCEL_GUARD_OWNER_PASSWORD', 'owner-5650'))
filtering = SensorFilter()
door_requested_open = False
forced_open = False
last_access_result = None
endpoint = {}
last_transmit = -1
malformed_count = 0
log_path = Path(__file__).resolve().parents[2] / 'results/runtime_events.jsonl'
log_path.parent.mkdir(exist_ok=True)
log_file = log_path.open('a' if state_path else 'w')
logged = 0
sensor_override = None

def read_sensors():
    distances = [s.getValue() for s in parcel_sensors]
    bolt = latch_position.getValue()
    if sensor_override:
        if sensor_override['mode'] == 'range':
            distances[0] = -1.0
        elif sensor_override['mode'] == 'frozen_bolt':
            bolt = sensor_override['value']
    return filtering.read(door_position.getValue(), bolt, distances, door_accel.getValues())


def execute(command, now, trusted=False):
    global door_requested_open, forced_open, logic, last_access_result, filtering, logged, endpoint, sensor_override
    if not isinstance(command, dict):
        raise ValueError('Command must be an object')
    action = command.get('action')
    if action == 'ack' and trusted:
        logic.acknowledge(command.get('session'), command.get('id'))
    elif action == 'endpoint_status' and trusted:
        endpoint = command
    elif action in ('owner_login', 'owner_logout', 'issue_code', 'revoke_code', 'clear_lockdown'):
        result = logic.security_command(command, now, sensors)
        reply = json.dumps({'type': 'security_reply', 'action': action, 'session': logic.session, **result})
        if trusted:
            security_reply_tx.send(reply.encode())
        else:
            robot.wwiSendText(reply)
    elif action == 'access':
        last_access_result = logic.request_access(command.get('code'), now, sensors,
                                                  command.get('request_id'), command.get('role'))
        if last_access_result:
            door_requested_open = True
    elif action == 'close':
        door_requested_open = forced_open = False
        logic.request_close(now)
    elif action == 'open' and logic.grant:
        door_requested_open = True
    elif action in ('link_off', 'link_on'):
        logic.set_link(action == 'link_on', now)
    elif action == 'actuator_override' and trusted:
        forced_open = bool(command.get('open'))
    elif action == 'actuator_jam' and trusted:
        latch_motor.setAvailableForce(0 if command.get('jammed') else 50)
        # Resist passive motion from the parent door while the bolt is blocked.
        latch_brake.setDampingConstant(10000 if command.get('jammed') else 0)
    elif action == 'door_jam' and trusted:
        door_motor.setAvailableTorque(0 if command.get('jammed') else 20)
    elif action == 'sensor_override' and trusted:
        mode = command.get('mode')
        if mode not in ('range', 'frozen_bolt', None):
            raise ValueError('Unknown sensor fixture')
        sensor_override = {'mode': mode, 'value': latch_position.getValue()} if mode else None
    elif action == 'reset_logic':
        if logic.security.enabled:
            logic._event('reset_denied', now, 'security mode uses owner-issued codes; reset cannot clear lockdown or credentials')
            return
        if logic.pending and not logic.storage_fault:
            logic._event('reset_denied', now, 'restore link and wait for pending events before starting a new session')
            return
        logic = Lockbox(auto_ack=False, start_time=now,
                        courier_valid_until=float(command.get('courier_ttl_s', 300)),
                        owner_valid_until=float(command.get('owner_ttl_s', 86400)),
                        state_path=state_path, restore=False, clock_epoch=clock_epoch)
        logic.previous = sensors
        if not sensors.closed:
            logic.request_close(now)
            logic._target(False, now)
        door_requested_open = forced_open = False
        last_access_result = None
        latch_motor.setAvailableForce(50)
        latch_brake.setDampingConstant(0)
        door_motor.setAvailableTorque(20)
        logged = 0
    elif action in ('parcel_in', 'parcel_out', 'impact', 'force_open', 'jam_latch', 'release_latch', 'jam_door', 'release_door', 'drop_acks', 'reset', 'restart_controller', 'sensor_fault', 'sensor_restore'):
        if action == 'impact' and command.get('severe'):
            command = {**command, 'force': 100, 'local': True}
        scene_tx.send(json.dumps(command).encode())
    else:
        raise ValueError('Unknown command')

frame = 0
motion_peak = 0
while robot.step(step_ms) != -1:
    now = robot.getTime()
    frame += 1
    sensors = read_sensors()
    motion_peak = max(motion_peak, max(abs(x) for x in door_accel.getValues()))
    message = robot.wwiReceiveText()
    while message is not None:
        try:
            execute(json.loads(message), now)
        except (ValueError, TypeError, OverflowError):
            malformed_count += 1
        message = robot.wwiReceiveText()
    while receiver.getQueueLength():
        try:
            execute(json.loads(receiver.getString()), now, True)
        except (ValueError, TypeError, OverflowError):
            malformed_count += 1
        receiver.nextPacket()
    logic.tick(now, sensors)
    latch_motor.setPosition(0.08 if logic.latch_target and sensors.valid and sensors.closed else 0.0)
    if not logic.grant:
        door_requested_open = False
    can_open = logic.grant and sensors.unlocked and sensors.valid and not logic.fault_reported
    door_motor.setPosition(1.2 if forced_open or (door_requested_open and can_open) else 0.0)
    secure = logic.status(now, sensors)['secured']
    led.set(0xff5959 if logic.status(now, sensors)['fault'] or logic.security.lockdown else (0x35dfb8 if secure else 0xffc45b))
    if logic.link_online and logic.pending and now - last_transmit >= CONFIG['ack_retry_s']:
        for event in logic.pending[:16]:
            event_tx.send(json.dumps(event).encode())
        last_transmit = now
    for event in logic.history[logged:]:
        log_file.write(json.dumps(event) + '\n')
    logged = len(logic.history)
    log_file.flush()
    if frame % 3 == 0:
        status = logic.status(now, sensors)
        status.update(event_kinds=[e['kind'] for e in logic.history], all_events=logic.history,
                      delivered_ids=[e['id'] for e in logic.delivered],
                      pending_ids=[e['id'] for e in logic.pending],
                      latch_target='locked' if logic.latch_target else 'unlocked',
                      door_angle_rad=round(door_position.getValue(), 4),
                      latch_position_m=round(latch_position.getValue(), 4),
                      parcel_distances_m=[round(s.getValue(), 4) for s in parcel_sensors],
                      door_accel_m_s2=[round(x, 3) for x in door_accel.getValues()],
                      last_access_result=last_access_result, malformed_commands=malformed_count, motion_peak_m_s2=motion_peak,
                      endpoint_ids=endpoint.get('sessions', {}).get(logic.session, []),
                      endpoint_duplicate_packets=endpoint.get('duplicates', 0))
        payload = encode_status(status)
        robot.wwiSendText(payload)
        emitter.send(payload.encode())
        motion_peak = 0
