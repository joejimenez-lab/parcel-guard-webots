"""Measured restart, invalid feedback, frozen feedback and access-impact trials."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lockbox.webots_harness import Harness

h = Harness()
checks = {}
error = None

def restart():
    count = h.latest['recovery_count']
    h.trace.clear()
    h.send('restart_controller')
    h.require(lambda s: s['recovery_count'] > count, 'Controller did not restore its checkpoint', limit=500)

try:
    h.advance(20)
    h.require(lambda s: s['secured'], 'Startup did not secure')
    h.send('link_off'); h.advance(8)
    for _ in range(10):
        h.send('impact'); h.advance(42)
    old_session = h.latest['session']
    expected = set(h.latest['pending_ids'])
    impacts_before = sum(e['kind'] == 'tamper' for e in h.latest['all_events'])
    restart()
    h.require(lambda s: s['secured'], 'Restart did not recover measured closure')
    checks['offline_restart'] = {
        'ten_impacts_recorded': impacts_before == 10,
        'same_session': h.latest['session'] == old_session,
        'all_pending_ids_retained': expected.issubset(h.latest['pending_ids']),
        'link_stays_offline': h.latest['link'] == 'offline',
        'no_access_grant': h.latest['grant'] == 'none',
    }
    # A new session must not silently discard the unacknowledged outbox.
    h.send('reset_logic'); h.advance(10)
    checks['reset_guard'] = {
        'session_preserved': h.latest['session'] == old_session,
        'queue_preserved': expected.issubset(h.latest['pending_ids']),
        'denial_explained': 'reset_denied' in h.latest['event_kinds'],
    }
    h.send('drop_acks', count=4); h.send('link_on')
    h.require(lambda s: s['pending'] == 0 and expected.issubset(s['endpoint_ids']), 'Recovered events did not drain')
    checks['recovered_ack_delivery'] = {
        'all_original_ids_received': expected.issubset(h.latest['endpoint_ids']),
        'unique_processing': len(h.latest['endpoint_ids']) == len(set(h.latest['endpoint_ids'])),
        'retry_observed': h.latest['endpoint_duplicate_packets'] > 0,
    }
    h.advance(15); h.reset()
    h.access('owner', 'restart-open')
    restart()
    h.require(lambda s: s['secured'], 'Restart during access did not return to secured')
    recovered = [s for s in h.trace if s['recovered']]
    h.send('access', role='owner', code='1357', request_id='owner-after-restart'); h.advance(12)
    checks['restart_during_access'] = {
        'used_code_retained': h.latest['owner_code_used'] and h.latest['last_access_result'] is False,
        'grant_cancelled': all(s['grant'] == 'none' for s in recovered),
        'bolt_waits_for_closure': all(s['latch_target'] == 'unlocked' for s in recovered if s['door'] != 'closed'),
        'measured_secure_recovery': h.latest['secured'],
    }
    h.advance(15); h.reset()
    h.send('sensor_fault'); h.require(lambda s: s['fault_reason'] == 'sensor', 'Invalid distance was not rejected')
    h.send('access', role='owner', code='1357', request_id='bad-sensor'); h.advance(10)
    checks['sensor_range_fault'] = {
        'cannot_claim_secure': not h.latest['secured'],
        'access_denied': h.latest['last_access_result'] is False,
        'reason_exposed': 'physical range' in h.latest['sensor_detail'],
    }
    h.send('sensor_restore'); h.require(lambda s: s['secured'], 'Valid feedback did not recover')
    checks['sensor_range_fault']['stable_recovery'] = True
    h.advance(15); h.reset()
    h.access('owner', 'frozen-feedback')
    h.send('sensor_fault', mode='frozen_bolt'); h.advance(10); h.send('close')
    h.require(lambda s: s['fault_reason'] == 'bolt', 'Frozen bolt feedback did not time out')
    checks['frozen_bolt_feedback'] = {'cannot_claim_secure': not h.latest['secured'], 'timeout_detected': True}
    h.send('sensor_restore'); h.require(lambda s: s['secured'], 'Restored bolt feedback did not recover')
    checks['frozen_bolt_feedback']['measured_recovery'] = True
    h.advance(15); h.reset()
    h.access('owner', 'strong-impact')
    h.advance(25)
    h.trace.clear()
    h.send('impact', severe=True)
    h.require(lambda s: any(e['kind'] == 'tamper' and 'severe impact' in e['detail'] for e in s['all_events']),
              'Strong impact during access was not detected')
    checks['impact_during_access'] = {
        'impact_classified_as_tamper': True,
        'authorization_revoked': h.latest['grant'] == 'none',
        'access_code_stays_used': h.latest['owner_code_used'],
    }
    h.require(lambda s: s['secured'], 'Strong-impact recovery did not secure')
    checks['impact_during_access']['measured_secure_recovery'] = True
except Exception as exc:
    error = str(exc)

h.finish({'passed': error is None and len(checks) == 7 and all(all(group.values()) for group in checks.values()),
          'checks': checks, 'runner_error': error, 'final_status': h.latest,
          'observed_peak_m_s2': max((s.get('motion_peak_m_s2', 0) for s in h.trace), default=0)}, 'webots_progress2.json')
