"""Targeted regressions for unsafe feedback, filtering, replay and ACK races."""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lockbox.core import Lockbox, Sensors
from lockbox.sensing import SensorFilter
checks={}
f=SensorFilter()
for _ in range(4): f.read(0,.08,[.60]*25,[0,0,9.81])
one=f.read(0,.08,[.20]*25,[0,0,9.81])
f.read(0,.08,[.60]*25,[0,0,9.81])
checks['single_frame_parcel_spike_rejected']=not one.parcel_present
for _ in range(3): s=f.read(0,.08,[.30]*25,[0,0,9.81])
checks['stable_parcel_detected']=s.parcel_present
for _ in range(8): s=f.read(0,.08,[.41]*25,[0,0,9.81])
checks['threshold_hysteresis']=s.parcel_present
for _ in range(3): s=f.read(0,.08,[.60]*25,[0,0,9.81])
checks['stable_empty_detected']=not s.parcel_present
s=f.read(0,float('nan'),[.60]*25,[0,0,9.81])
b=Lockbox();b.tick(0,s)
checks['nonfinite_feedback_fails_closed']=not b.status(0,s)['secured'] and not b.request_access('1357',0,s,'nan')
b=Lockbox();b.request_access('1357',0,Sensors(),'midstroke')
b.tick(2.1,Sensors(latch_locked=False,latch_unlocked=False))
checks['midstroke_is_not_unlocked']=b.fault_reported and b.status(2.1,Sensors(latch_locked=False,latch_unlocked=False))['latch']=='moving'
b=Lockbox();b.request_access('1357',0,Sensors(),'first')
checks['concurrent_second_access_denied']=not b.request_access('2468',0,Sensors(),'second')
checks['missing_id_denied']=not Lockbox().request_access('1357',0,Sensors(),None)
checks['role_scope_denied']=not Lockbox().request_access('2468',0,Sensors(),'wrong-role','owner')
b=Lockbox(auto_ack=False);e=b._event('tamper',0)
checks['event_waits_for_ack']=len(b.pending)==1 and not b.delivered
checks['wrong_session_ack_ignored']=not b.acknowledge('other',e['id'])
b.set_link(False,1)
checks['offline_ack_ignored']=not b.acknowledge(b.session,e['id'])
b.set_link(True,2);b.acknowledge(b.session,e['id'])
checks['duplicate_ack_idempotent']=not b.acknowledge(b.session,e['id']) and len(b.delivered)==1
b=Lockbox(start_time=100,courier_valid_until=2)
checks['ttl_relative_to_issue_time']=b.request_access('2468',101,Sensors(),'valid') and not Lockbox(start_time=100,courier_valid_until=2).request_access('2468',103,Sensors(),'expired')
# Startup and recovery require three consecutive usable samples.
f=SensorFilter()
a=f.read(0,.08,[.20]*25,[0,0,9.81])
b=Lockbox()
checks['startup_access_denied']=not a.valid and not b.request_access('2468',0,a,'startup')
f.read(0,.08,[.20]*25,[0,0,9.81])
a=f.read(0,.08,[.20]*25,[0,0,9.81])
checks['startup_occupied_resolved']=a.valid and a.parcel_present and not b.request_access('2468',.1,a,'occupied')
f=SensorFilter()
for _ in range(3): f.read(0,.08,[.60]*25,[0,0,9.81])
f.read(0,.08,[.20]*25,[0,0,9.81]); f.read(0,.08,[.20]*25,[0,0,9.81])
f.read(0,float('nan'),[.20]*25,[0,0,9.81])
a=f.read(0,.08,[.20]*25,[0,0,9.81])
checks['invalid_gap_breaks_debounce']=not a.valid and not a.parcel_present
checks['missing_sensor_array_invalid']=not SensorFilter().read(0,.08,[],[0,0,9.81]).valid
checks['exact_expiry_rejected']=not Lockbox(courier_valid_until=2).request_access('2468',2,Sensors(),'boundary')
for ttl in (float('nan'),float('inf'),-1):
 try: Lockbox(courier_valid_until=ttl)
 except ValueError: checks[f'invalid_ttl_{ttl}_rejected']=True
 else: checks[f'invalid_ttl_{ttl}_rejected']=False
b=Lockbox(); b.request_access('1357',0,Sensors(),'expires-open')
opened=Sensors(door_open=True,latch_locked=False,door_closed=False,latch_unlocked=True)
b.tick(1,opened); b.tick(20,opened)
checks['deadline_revokes_open_grant']=b.grant is None and b.status(20,opened)['phase']=='CLOSING'
b.tick(23.1,opened)
checks['door_jam_fault_without_bolt_extension']=b.door_fault and not b.latch_target and not b.status(23.1,opened)['secured']
b.tick(24,Sensors(door_open=True,parcel_present=True,latch_locked=False))
checks['late_parcel_movement_is_tamper']=b.history[-1]['kind']=='tamper'
b.tick(25,Sensors(parcel_present=True,latch_locked=False)); b.tick(26,Sensors(parcel_present=True))
checks['door_recovery_measured']=not b.door_fault and b.status(26,Sensors(parcel_present=True))['secured']
b=Lockbox(); b.request_access('1357',0,Sensors(),'cancel'); b.request_close(.1); b.tick(.1,Sensors())
checks['early_close_revokes_grant']=b.grant is None and b.status(.1,Sensors())['secured']
b=Lockbox(); b.request_access('1357',0,Sensors(),'sensor-loss'); b.tick(.5,opened)
b.tick(.6,Sensors(valid=False))
checks['sensor_loss_revokes_grant']=b.grant is None and not b.status(.6,Sensors(valid=False))['secured']
b.tick(.7,opened)
checks['sensor_recovery_no_false_door_edge']=not any(e['kind']=='tamper' for e in b.history)
from lockbox.protocol import encode_status
payload=encode_status({'values':[1,float('nan'),float('inf')]})
checks['nonfinite_telemetry_is_json_null']=json.loads(payload)=={'values':[1,None,None]}
b=Lockbox(); b.tick(0,Sensors())
for at in (.1,.2,.3):
 b.request_close(at); b.tick(at,Sensors())
b.tick(.4,Sensors(impact=True))
checks['redundant_close_does_not_suppress_impact']=any(e['kind']=='tamper' for e in b.history)
report={'passed':all(checks.values()),'checks':checks}
(ROOT/'results/robustness.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
raise SystemExit(0 if report['passed'] else 1)
