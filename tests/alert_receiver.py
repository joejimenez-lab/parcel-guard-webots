"""Test durable alert receipts, identity isolation and recovery from a failed write."""
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lockbox.alert_receiver import AlertReceiver


class AlertReceiverTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        directory = temp.name
        self.path = Path(directory) / 'receiver.sqlite3'
        self.alert = {'session': 'box-a', 'id': 1, 'kind': 'tamper'}

    def open_receiver(self):
        receiver = AlertReceiver(self.path)
        self.addCleanup(receiver.close)
        return receiver

    def test_retry_after_reopen_preserves_first_receipt_and_payload(self):
        with closing(AlertReceiver(self.path)) as first:
            self.assertTrue(first.record(self.alert))
        receiver = self.open_receiver()
        self.assertFalse(receiver.record({**self.alert, 'kind': 'different'}))
        self.assertEqual(receiver.sessions(), {'box-a': [1]})
        with closing(sqlite3.connect(self.path)) as connection:
            rows = connection.execute('SELECT event_json FROM receipts').fetchall()
        self.assertEqual([json.loads(payload) for payload, in rows], [self.alert])

    def test_live_receivers_share_identity_without_confusing_sessions(self):
        first = self.open_receiver()
        second = self.open_receiver()
        self.assertTrue(first.record(self.alert))
        self.assertFalse(second.record(self.alert))
        self.assertTrue(second.record({**self.alert, 'session': 'box-b'}))
        self.assertEqual(first.sessions(), {'box-a': [1], 'box-b': [1]})

    def test_storage_failure_does_not_report_acceptance(self):
        receiver = self.open_receiver()
        with closing(sqlite3.connect(self.path)) as other_writer:
            other_writer.execute('BEGIN IMMEDIATE')
            with self.assertRaises(sqlite3.OperationalError):
                receiver.record(self.alert)
            other_writer.rollback()
        self.assertEqual(receiver.sessions(), {})
        self.assertTrue(receiver.record(self.alert))


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AlertReceiverTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {
        'passed': result.wasSuccessful(),
        'tests_run': result.testsRun,
        'failures': [str(test) for test, _ in result.failures],
        'errors': [str(test) for test, _ in result.errors],
    }
    (ROOT/'results/alert_receiver.json').write_text(json.dumps(report, indent=2) + '\n')
    raise SystemExit(0 if report['passed'] else 1)
