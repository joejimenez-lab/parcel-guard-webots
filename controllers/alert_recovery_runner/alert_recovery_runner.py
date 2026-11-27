"""Run a lost-ACK test with real Webots controller restarts on both sides."""
from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lockbox.webots_harness import Harness


def persisted_alerts(path, session, event_id):
    with closing(sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)) as connection:
        return [json.loads(row[0]) for row in connection.execute(
            'SELECT event_json FROM receipts WHERE session = ? AND event_id = ?', (session, event_id)
        )]


def scenario(h, evidence):
    path = Path(os.environ['PARCEL_GUARD_RECEIVER_PATH'])
    h.require(lambda s: s['secured'] and s['endpoint_instance'], 'Both controllers did not start')
    h.send('drop_acks', count=100)
    h.advance(8)
    h.send('impact')
    h.require(
        lambda s: 'tamper' in s['event_kinds'] and s['endpoint_dropped_acks'] > 0
        and any(event['kind'] == 'tamper' and event['id'] in s['endpoint_ids'] for event in s['all_events']),
        'The receiver did not record the tamper alert and drop its ACK',
    )
    alert, = [event for event in h.latest['all_events'] if event['kind'] == 'tamper']
    session, event_id = alert['session'], alert['id']
    evidence['alert'] = {'session': session, 'id': event_id, 'kind': alert['kind']}

    # Pause the link so the restarted receiver cannot ACK until both fresh
    # controller instances have published restored state.
    h.send('link_off')
    h.require(lambda s: s['link'] == 'offline', 'Link did not pause')
    h.advance(20)
    before = h.latest
    stored_before = persisted_alerts(path, session, event_id)
    evidence['before_restart'] = {
        'receiver_receipts': len(stored_before),
        'acknowledgments_dropped': before['endpoint_dropped_acks'],
        'sender_pending': event_id in before['pending_ids'],
        'sender_acknowledgments': before['delivered_ids'].count(event_id),
    }
    if stored_before != [alert] or event_id not in before['pending_ids'] or event_id in before['delivered_ids']:
        raise AssertionError('Expected one durable alert still pending at the sender before restarting')

    h.robot.getFromDef('FIXTURE').restartController()
    h.robot.getFromDef('BOX').restartController()
    h.require(
        lambda s: s['recovery_count'] > before['recovery_count']
        and s['endpoint_instance'] and s['endpoint_instance'] != before['endpoint_instance']
        and s['endpoint_ids'].count(event_id) == 1,
        'Both restarted controllers did not report restored state',
        limit=500,
    )
    restored = h.latest
    evidence['after_restart_before_retry'] = {
        'sender_restarted': restored['recovery_count'] > before['recovery_count'],
        'receiver_restarted': restored['endpoint_instance'] != before['endpoint_instance'],
        'session_preserved': restored['session'] == session,
        'link_still_paused': restored['link'] == 'offline',
        'sender_pending': event_id in restored['pending_ids'],
        'receiver_receipts': restored['endpoint_ids'].count(event_id),
        'receiver_duplicate_packets': restored['endpoint_duplicate_packets'],
        'sender_acknowledgments': restored['delivered_ids'].count(event_id),
    }

    h.send('link_on')
    h.require(
        lambda s: event_id in s['delivered_ids'] and s['pending'] == 0
        and s['endpoint_duplicate_packets'] > 0,
        'The restarted receiver did not recognize and ACK the retry',
    )
    final = h.latest
    stored_after = persisted_alerts(path, session, event_id)
    evidence['after_retry'] = {
        'receiver_receipts': len(stored_after),
        'receiver_duplicate_packets': final['endpoint_duplicate_packets'],
        'sender_acknowledgments': final['delivered_ids'].count(event_id),
        'sender_queue': final['pending'],
    }
    return {
        'ack_lost_after_durable_receipt': before['endpoint_dropped_acks'] > 0,
        'both_controllers_restarted': evidence['after_restart_before_retry']['sender_restarted']
        and evidence['after_restart_before_retry']['receiver_restarted'],
        'same_alert_restored_before_retry': restored['session'] == session
        and restored['link'] == 'offline' and event_id in restored['pending_ids']
        and event_id not in restored['delivered_ids'] and restored['endpoint_duplicate_packets'] == 0,
        'retry_seen_by_restarted_receiver': final['endpoint_instance'] == restored['endpoint_instance']
        and final['endpoint_duplicate_packets'] > 0,
        'one_durable_alert': stored_after == stored_before == [alert]
        and final['endpoint_ids'].count(event_id) == 1 and not final['endpoint_storage_fault'],
        'one_sender_acknowledgment_and_empty_queue':
        final['delivered_ids'].count(event_id) == 1 and final['pending'] == 0,
    }


harness = Harness()
evidence = {}
checks = {}
error = None
try:
    checks = scenario(harness, evidence)
except Exception as exc:
    error = str(exc)
harness.finish({'passed': error is None and bool(checks) and all(checks.values()),
                'checks': checks, 'runner_error': error, 'evidence': evidence},
               'webots_alert_recovery.json')
