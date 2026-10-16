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
report={'passed':all(checks.values()),'checks':checks}
(ROOT/'results/robustness.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
raise SystemExit(0 if report['passed'] else 1)
