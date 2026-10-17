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
    # Local access, sensing, closure and logging must work while the link is off.
    h.reset(); h.send('link_off'); h.advance(10)
    h.access('courier','offline-courier'); h.send('parcel_in'); h.advance(15)
    detected_pending = h.latest['delivery_pending'] and 'delivery' not in h.latest['event_kinds']
    h.send('jam_latch'); h.advance(8); h.send('close')
    h.require(lambda s:s['fault_reason']=='bolt','Pending delivery did not report a blocked bolt')
    blocked_unconfirmed = not h.latest['secured'] and 'delivery' not in h.latest['event_kinds']
    h.send('release_latch'); h.require(lambda s:s['secured'],'Delivery did not secure after release')
    confirmed = h.latest['event_kinds'].count('delivery')==1 and not h.latest['delivery_pending']
    h.access('owner','offline-owner'); h.send('parcel_out'); h.advance(15); h.close()
    local_retrieval = h.latest['event_kinds'].count('retrieval')==1 and h.latest['parcel']=='empty'
    queued = len(h.latest['pending_ids'])==len(h.latest['all_events']) and not h.latest['delivered_ids']
    expected = set(h.latest['pending_ids'])
    h.send('link_on'); h.require(lambda s:s['pending']==0 and expected.issubset(s['endpoint_ids']),'Offline workflow events did not drain')
    recovered = expected.issubset(h.latest['endpoint_ids']) and len(h.latest['endpoint_ids'])==len(set(h.latest['endpoint_ids']))
    checks['offline_delivery_and_retrieval'] = {'presence_pending':detected_pending,'blocked_lock_no_delivery':blocked_unconfirmed,
        'delivery_after_measured_lock':confirmed,'local_retrieval':local_retrieval,'all_events_retained':queued,'recovered_once':recovered}
    h.send('access',code='1357',role='owner',request_id='owner-reuse'); h.advance(12)
    checks['owner_reuse'] = {'denied':h.latest['last_access_result'] is False and h.latest['secured'],
        'reason':h.latest['all_events'][-1]['detail']=='owner code already used'}
    h.reset(); h.access('owner','reset-open'); old_session=h.latest['session']; h.trace.clear()
    h.send('reset_logic'); h.require(lambda s:s['session']!=old_session,'Open-door reset did not arrive')
    h.require(lambda s:s['secured'],'Open-door reset did not recover')
    reset_samples=[s for s in h.trace if s['session']!=old_session]
    checks['reset_while_open'] = {'fresh_session':bool(reset_samples),
        'no_grant_survives':all(s['grant']=='none' for s in reset_samples),
        'bolt_retracted_until_closed':all(s['latch_target']=='unlocked' for s in reset_samples if s['door']!='closed'),
        'recovered_empty_and_secured':h.latest['secured'] and h.latest['parcel']=='empty'}
except Exception as exc:
    error=str(exc)
h.finish({'passed':error is None and len(checks)==6 and all(all(v.values()) for v in checks.values()),
          'checks':checks,'runner_error':error,'final_status':h.latest},'webots_edge_cases.json')
