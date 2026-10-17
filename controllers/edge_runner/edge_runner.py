"""Simulator regressions for expired grants, door faults and malformed input."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from lockbox.webots_harness import Harness
h=Harness()
checks={}
error=None
try:
    h.advance(15)
    h.reset()
    h.access('owner','door-timeout')
    h.advance(30)
    h.send('jam_door'); h.advance(8)
    h.require(lambda s:s['fault_reason']=='door','Open door did not report timeout',limit=900)
    expired = (h.latest['grant']=='none' and not h.latest['secured'] and h.latest['latch']=='unlocked')
    h.send('parcel_in'); h.advance(15)
    late_movement = any(e['kind']=='tamper' and e['detail']=='unapproved parcel movement' for e in h.latest['all_events'])
    h.send('release_door')
    h.require(lambda s:s['secured'],'Door fault did not recover after release')
    checks['door_timeout'] = {'expired_grant_revoked':expired,'late_movement_flagged':late_movement,
                              'measured_recovery':'door_recovered' in h.latest['event_kinds']}
    h.send('parcel_out'); h.advance(15)
    h.reset()
    h.send('access',role='owner',code='1357',request_id='cancel-early')
    h.advance(3)
    h.send('close')
    h.require(lambda s:s['secured'],'Early close did not cancel access')
    h.advance(60)
    checks['early_close'] = {'grant_cancelled':h.latest['grant']=='none','stays_secured':h.latest['secured']}
    malformed_before = h.latest['malformed_commands']
    h.tx.send(b'not-json'); h.tx.send(b'[]')
    h.tx.send(b'{"action":"reset_logic","courier_ttl_s":"nan"}')
    h.advance(15)
    checks['malformed_commands'] = {'counted':h.latest['malformed_commands']==malformed_before+3,
                                    'still_secured':h.latest['secured']}
except Exception as exc:
    error=str(exc)
h.finish({'passed':error is None and len(checks)==3 and all(all(v.values()) for v in checks.values()),
          'checks':checks,'runner_error':error,'final_status':h.latest},'webots_edge_cases.json')
