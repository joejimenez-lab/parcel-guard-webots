"""Recovery and fault-injection regressions for the second progress report."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lockbox.core import Lockbox, Sensors
from lockbox.sensing import SensorFilter


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / 'state.json'

    def box(self, now=0):
        return Lockbox(auto_ack=False, state_path=self.path, start_time=now)

    def test_abrupt_process_exit_preserves_offline_events(self):
        program = """
import os, sys
from lockbox.core import Lockbox, Sensors
b=Lockbox(auto_ack=False,state_path=sys.argv[1])
b.set_link(False,1)
for i in range(10): b.tick(2+i*1.1,Sensors(impact=True))
os._exit(0)
"""
        subprocess.run([sys.executable, '-c', program, str(self.path)], cwd=ROOT, check=True)
        b = self.box(20)
        self.assertEqual(sum(e['kind'] == 'tamper' for e in b.pending), 10)
        self.assertFalse(b.link_online)
        self.assertTrue(b.recovered)

    def test_recovery_keeps_session_and_monotonic_ids(self):
        b = self.box(); b._event('tamper', 1)
        session, last = b.session, b.next_id
        recovered = self.box(2)
        self.assertEqual(recovered.session, session)
        self.assertEqual(recovered.history[-1]['id'], last)

    def test_ack_commit_survives_another_restart(self):
        b = self.box(); event = b._event('tamper', 1)
        b.acknowledge(b.session, event['id'])
        recovered = self.box(2)
        self.assertNotIn(event, recovered.pending)
        self.assertIn(event, recovered.delivered)

    def test_used_owner_code_survives_restart(self):
        b = self.box(); self.assertTrue(b.request_access('1357', 1, Sensors(), 'owner'))
        b = self.box(2); b.tick(2.1, Sensors())
        self.assertFalse(b.request_access('1357', 3, Sensors(), 'owner-again'))
        self.assertEqual(b.history[-1]['detail'], 'owner code already used')

    def test_used_courier_code_survives_restart(self):
        b = self.box(); b.request_access('2468', 1, Sensors(), 'courier')
        b = self.box(2); b.tick(2.1, Sensors())
        self.assertFalse(b.request_access('2468', 3, Sensors(), 'courier-again'))
        self.assertEqual(b.history[-1]['detail'], 'courier code already used')

    def test_replay_id_survives_restart(self):
        self.box().request_access('wrong', 1, Sensors(), 'old-id')
        b = self.box(2)
        self.assertFalse(b.request_access('1357', 3, Sensors(), 'old-id'))
        self.assertEqual(b.history[-1]['detail'], 'replayed request ID')

    def test_cooldown_survives_restart(self):
        b = self.box()
        for i in range(5): b.request_access('wrong', i, Sensors(), f'wrong-{i}')
        b = self.box(5); b.tick(5.1, Sensors())
        self.assertFalse(b.request_access('1357', 6, Sensors(), 'paused'))
        self.assertTrue(b.request_access('1357', 65, Sensors(), 'after-pause'))

    def test_failure_counter_survives_restart(self):
        b = self.box()
        for i in range(4): b.request_access('wrong', i, Sensors(), f'wrong-{i}')
        b = self.box(4); b.request_access('wrong', 5, Sensors(), 'fifth')
        self.assertEqual(b.locked_until, 65)

    def test_access_is_cancelled_and_open_bolt_stays_retracted(self):
        self.box().request_access('1357', 1, Sensors(), 'open')
        b = self.box(2)
        opened = Sensors(door_open=True, latch_locked=False)
        b.tick(2.1, opened)
        self.assertIsNone(b.grant)
        self.assertFalse(b.latch_target)
        self.assertFalse(b.status(2.1, opened)['secured'])

    def test_clock_rewind_expires_codes(self):
        b = self.box(100); b._event('tamper', 101)
        b = self.box(0); b.tick(.1, Sensors())
        self.assertTrue(b.clock_rewound)
        self.assertFalse(b.request_access('1357', 1, Sensors(), 'rewound'))

    def test_clock_rewind_keeps_cooldown(self):
        b = self.box(100)
        for i in range(5): b.request_access('wrong', 101+i, Sensors(), str(i))
        b = self.box(0)
        self.assertEqual(b.locked_until, 60)

    def test_new_world_epoch_expires_codes_even_if_clock_is_later(self):
        Lockbox(state_path=self.path, clock_epoch='world-one')
        b = Lockbox(state_path=self.path, clock_epoch='world-two', start_time=10)
        self.assertTrue(b.clock_rewound)
        b.tick(10, Sensors())
        self.assertFalse(b.request_access('1357', 11, Sensors(), 'new-world'))

    def test_corrupt_file_denies_access_and_is_preserved(self):
        self.path.write_text('{broken')
        b = self.box()
        self.assertTrue(b.storage_fault)
        self.assertFalse(b.request_access('1357', 1, Sensors(), 'corrupt'))
        self.assertFalse(b.status(1, Sensors())['secured'])
        self.assertEqual(self.path.read_text(), '{broken')

    def test_checksum_failure_denies_access(self):
        self.box()
        record = json.loads(self.path.read_text())
        record['payload']['state']['owner_used'] = True
        self.path.write_text(json.dumps(record))
        self.assertTrue(self.box(1).storage_fault)

    def test_write_failure_cancels_access(self):
        b = self.box()
        with patch.object(b.store, 'save', side_effect=OSError('disk full')):
            self.assertFalse(b.request_access('1357', 1, Sensors(), 'full'))
        self.assertIsNone(b.grant)
        self.assertEqual(b.status(1, Sensors())['fault_reason'], 'storage')

    def test_failed_atomic_replace_keeps_previous_file(self):
        b = self.box(); original = self.path.read_bytes()
        with patch('lockbox.storage.os.replace', side_effect=OSError('interrupted write')):
            b._event('tamper', 1)
        self.assertEqual(self.path.read_bytes(), original)
        self.assertEqual(len(list(self.path.parent.iterdir())), 1)

    def test_recovered_store_can_commit_new_events(self):
        b = self.box(); b._event('tamper', 1)
        b = self.box(2); event = b._event('tamper', 3)
        self.assertIn(event, self.box(4).pending)


class SensorAndImpactTests(unittest.TestCase):
    def stable(self, **changed):
        values = dict(door=0, bolt=.08, distances=[.6]*25, acceleration=[0, 0, 9.81])
        values.update(changed)
        filtering = SensorFilter()
        for _ in range(3): sample = filtering.read(**values)
        return sample

    def test_negative_distance_is_invalid(self):
        self.assertFalse(self.stable(distances=[-.01]+[.6]*24).valid)

    def test_out_of_range_distance_is_invalid(self):
        self.assertFalse(self.stable(distances=[.9]*25).valid)

    def test_impossible_joint_positions_are_invalid(self):
        self.assertFalse(self.stable(door=2).valid)
        self.assertFalse(self.stable(bolt=.2).valid)

    def test_range_fault_needs_three_good_samples_to_recover(self):
        f = SensorFilter()
        f.read(0, .08, [-1]*25, [0,0,9.81])
        for _ in range(2): self.assertFalse(f.read(0,.08,[.6]*25,[0,0,9.81]).valid)
        self.assertTrue(f.read(0,.08,[.6]*25,[0,0,9.81]).valid)

    def test_normal_access_motion_stays_approved(self):
        b = Lockbox(); b.request_access('1357', 0, Sensors(), 'normal')
        b.tick(1, self.stable(door=1.2, bolt=0, acceleration=[20,0,9.81]))
        self.assertFalse(any(e['kind'] == 'tamper' for e in b.history))

    def test_severe_impact_during_access_revokes_grant(self):
        b = Lockbox(); b.request_access('1357', 0, Sensors(), 'impact')
        b.tick(1, self.stable(door=1.2, bolt=0, acceleration=[40,0,9.81]))
        self.assertIsNone(b.grant)
        self.assertIn('tamper', [e['kind'] for e in b.history])

    def test_severe_impact_is_not_hidden_by_close_grace(self):
        b = Lockbox(); b.authorized_motion_until = 10
        b.tick(1, self.stable(acceleration=[40,0,9.81]))
        self.assertEqual(b.history[-1]['kind'], 'tamper')

    def test_severe_impact_is_not_hidden_by_another_sensor_fault(self):
        b = Lockbox(); b.request_access('1357', 0, Sensors(), 'impact-fault')
        b.tick(1, self.stable(distances=[-1]*25, acceleration=[40,0,9.81]))
        self.assertIsNone(b.grant)
        self.assertIn('tamper', [e['kind'] for e in b.history])

    def test_frozen_bolt_during_motion_reports_timeout(self):
        b = Lockbox(); b.request_access('1357', 0, Sensors(), 'freeze')
        b.tick(2.1, Sensors())
        self.assertEqual(b.status(2.1, Sensors())['fault_reason'], 'bolt')


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {'passed': result.wasSuccessful(), 'tests_run': result.testsRun,
              'failures': [str(test) for test, _ in result.failures],
              'errors': [str(test) for test, _ in result.errors],
              'method': 'temporary local stores, abrupt child-process exit, injected disk errors and deterministic sensor samples'}
    (ROOT/'results/progress2_regressions.json').write_text(json.dumps(report, indent=2)+'\n')
    raise SystemExit(0 if report['passed'] else 1)
