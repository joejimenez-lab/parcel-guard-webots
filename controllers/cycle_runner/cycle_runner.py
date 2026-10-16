"""Physical motor, measured event latency, ACK recovery, and access evaluation."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lockbox.webots_harness import Harness
h = Harness()
checks = {}
error = None
try:
    h.advance(15)
    cycles = []
    for i in range(100):
        start = h.robot.getTime()
        h.access('owner',f'cycle-{i}')
        opened = h.robot.getTime()
        h.close()
        cycles.append({'cycle':i,'unlock_and_open_s':opened-start,'full_cycle_s':h.robot.getTime()-start,
                       'door_rad':h.latest['door_angle_rad'],'bolt_m':h.latest['latch_position_m'],'secured':h.latest['secured']})
    checks['motor_cycles'] = {'successful':sum(t['secured'] for t in cycles),'attempted':100,'target':99,'trials':cycles}
    latencies = []
    h.advance(30)
    for i in range(30):
        prior = set(h.observed)
        start = h.robot.getTime()
        h.send('impact')
        h.require(lambda s:any(k not in prior and e['kind']=='tamper' and e['detail']=='impact detected' for k,(e,_) in h.observed.items()),'Impact did not queue an alert')
        matches = [(e,seen) for k,(e,seen) in h.observed.items() if k not in prior and e['kind']=='tamper' and e['detail']=='impact detected']
        event,seen = matches[0]
        latencies.append({'trial':i,'event_id':event['id'],'sensor_sample_s':event['sensor_time'],
                          'queued_s':event['time'],'sensor_to_queue_s':event['queue_latency_s'],
                          'stimulus_to_observer_s':round(seen-start,6)})
        h.advance(40)
    sensor_latency = sorted(t['sensor_to_queue_s'] for t in latencies)
    checks['alert_latency'] = {'within_1s':sum(v<1 for v in sensor_latency),'trials':30,'target':29,
                              'median_s':sensor_latency[15],'p95_s':sensor_latency[28],'max_s':max(sensor_latency),
                              'max_stimulus_to_observer_s':max(t['stimulus_to_observer_s'] for t in latencies),
                              'definition':'First sampled impact threshold crossing to synchronous local outbox insertion; simulated time; excludes transport/rendering', 'details':latencies}
    outages = []
    for i in range(10):
        h.require(lambda s:s['pending']==0,'Pre-outage queue did not drain')
        h.advance(10)
        before = set(h.latest['delivered_ids'])
        prior_events = set(e['id'] for e in h.latest['all_events'])
        h.send('link_off'); h.advance(12)
        for _ in range(10):
            h.send('impact'); h.advance(40)
        expected = [e['id'] for e in h.latest['all_events'] if e['id'] not in prior_events and e['kind']=='tamper' and e['detail']=='impact detected']
        retained = len(expected)==10 and all(eid in h.latest['pending_ids'] for eid in expected) and set(h.latest['delivered_ids'])==before
        started = h.robot.getTime()
        h.send('link_on')
        h.require(lambda s:s['pending']==0 and all(eid in s['endpoint_ids'] for eid in expected),'Reconnect lost an expected event')
        ids = h.latest['delivered_ids']; endpoint = h.latest['endpoint_ids']
        recovered = retained and all(ids.count(eid)==endpoint.count(eid)==1 for eid in expected)
        outages.append({'outage':i,'expected_tamper_ids':expected,'retained_offline':retained,'recovered_once':recovered,
                        'reconnect_drain_s':round(h.robot.getTime()-started,6)})
    checks['connection_recovery'] = {'successful_outages':sum(t['recovered_once'] for t in outages),'target':10,
                                    'events_per_outage':10,'expected_events':100,'recovered_events':sum(len(t['expected_tamper_ids']) for t in outages if t['recovered_once']),
                                    'outages':outages}
    dup_before = h.latest['endpoint_duplicate_packets']
    h.send('drop_acks',count=5); h.advance(8)
    h.send('impact'); h.advance(60)
    checks['lost_ack_retry'] = {'retried':h.latest['endpoint_duplicate_packets']>dup_before,
                               'queue_drained':h.latest['pending']==0,
                               'receiver_ids_unique':len(h.latest['endpoint_ids'])==len(set(h.latest['endpoint_ids']))}
    h.access('owner','locking-jam')
    h.send('jam_latch'); h.advance(8)
    h.send('close'); h.advance(130)
    locked_fault = h.latest['phase']=='FAULT' and h.latest['door']=='closed' and not h.latest['secured'] and h.latest['latch']!='locked'
    h.send('release_latch'); h.require(lambda s:s['secured'],'Locking fault did not recover from measured feedback')
    recovered_lock = 'latch_recovered' in h.latest['event_kinds']
    h.send('jam_latch'); h.advance(8)
    h.send('access',role='owner',code='1357',request_id='unlocking-jam'); h.advance(100)
    unlock_fault = h.latest['phase']=='FAULT' and not h.latest['secured'] and h.latest['door']=='closed'
    h.send('release_latch'); h.require(lambda s:s['door_angle_rad']>=1,'Unlock fault did not recover')
    h.close()
    checks['latch_jam'] = {'blocked_lock_fault':locked_fault,'blocked_unlock_fault':unlock_fault,'measured_recovery':recovered_lock,'recovered_to_secured':h.latest['secured']}
    access_trials = []
    for category in ('invalid','expired','reused','wrong_role','replay'):
        for i in range(6):
            h.reset(courier_ttl_s=0 if category=='expired' else 300)
            code,role,request_id = '2468','courier',f'{category}-{i}'
            if category=='invalid': code='0000'
            elif category=='expired':
                if i%2: h.send('link_off'); h.advance(8)
            elif category=='reused': h.access('courier',f'first-use-{i}'); h.close()
            elif category=='wrong_role':
                code,role = ('1357','courier') if i%2 else ('2468','owner')
            elif category=='replay':
                code,role = '1357','owner'
                h.access(role,request_id); h.close()
            grants_before = h.latest['event_kinds'].count('access_granted')
            h.send('access',code=code,role=role,request_id=request_id)
            h.advance(16)
            denied = h.latest['last_access_result'] is False
            unauthorized = h.latest['event_kinds'].count('access_granted')-grants_before
            access_trials.append({'category':category,'trial':i,'denied':denied,'unauthorized_unlocks':unauthorized,
                                  'secured':h.latest['secured'],'reason':next((e['detail'] for e in reversed(h.latest['events']) if e['kind']=='access_denied'),None)})
            if category=='expired' and i%2: h.send('link_on'); h.advance(15)
    checks['access_security'] = {'trials':30,'categories':{c:sum(t['denied'] and t['secured'] and t['unauthorized_unlocks']==0 for t in access_trials if t['category']==c) for c in ('invalid','expired','reused','wrong_role','replay')},
                                'unauthorized_unlocks':sum(t['unauthorized_unlocks'] for t in access_trials),'details':access_trials}
    h.reset()
    for i in range(5): h.send('access',code='wrong',role='owner',request_id=f'cooldown-{i}'); h.advance(4)
    paused = h.latest['entry_paused_s']>59
    h.send('access',code='1357',role='owner',request_id='paused-valid'); h.advance(6)
    valid_blocked = h.latest['last_access_result'] is False and h.latest['secured']
    h.require(lambda s:s['entry_paused_s']==0,'Cooldown did not expire',limit=2000)
    h.access('owner','after-cooldown'); h.close()
    checks['cooldown'] = {'five_failures_pause_60s':paused,'valid_code_blocked_during_pause':valid_blocked,'valid_code_works_after_pause':h.latest['secured']}
    h.reset()
    h.access('owner','autoclose')
    h.require(lambda s:s['secured'],'Access window did not automatically secure the box',limit=800)
    checks['access_timeout'] = {'auto_closed_and_secured':h.latest['secured']}
except Exception as e:
    error = str(e)
passed = (error is None and checks.get('motor_cycles',{}).get('successful',0)>=99
          and checks.get('alert_latency',{}).get('within_1s',0)>=29
          and checks.get('connection_recovery',{}).get('recovered_events',0)==100
          and all(checks.get('lost_ack_retry',{'missing':False}).values())
          and all(checks.get('latch_jam',{'missing':False}).values())
          and checks.get('access_security',{}).get('unauthorized_unlocks',-1)==0
          and all(v==6 for v in checks.get('access_security',{}).get('categories',{'missing':0}).values())
          and all(checks.get('cooldown',{'missing':False}).values())
          and checks.get('access_timeout',{}).get('auto_closed_and_secured',False))
h.finish({'passed':passed,'checks':checks,'runner_error':error,'simulation_time_s':h.robot.getTime(),'timestep_ms':h.dt},'webots_benchmark.json')
