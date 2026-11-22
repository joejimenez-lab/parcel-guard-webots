"""Password sign-in, credential controls and persistent lockdown regressions."""
import base64
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lockbox.core import Lockbox, Sensors

CREDENTIAL_KEY = '3132333435363738393031323334353637383930'
PASSWORD = 'test-owner-password'


class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/'state.json'
        self.box = Lockbox(secure_mode=True, owner_password=PASSWORD, credential_key=CREDENTIAL_KEY,
                           state_path=self.path, auto_ack=False)

    def login(self, box=None, now=1):
        return (box or self.box).security_command({'action': 'owner_login', 'password': PASSWORD}, now, Sensors())

    def issue(self, token, role='courier', now=2, ttl=300, box=None):
        return (box or self.box).security_command({'action': 'issue_code', 'token': token,
                     'role': role, 'ttl_s': ttl}, now, Sensors())

    def restart(self, now=5):
        return Lockbox(secure_mode=True, owner_password=PASSWORD, credential_key=CREDENTIAL_KEY,
                       state_path=self.path, auto_ack=False, start_time=now)

    def test_password_only_sign_in_requires_no_other_fields(self):
        self.assertTrue(self.login()['ok'])

    def test_wrong_password_cannot_sign_in(self):
        result=self.box.security_command({'action':'owner_login','password':'wrong'},1,Sensors())
        self.assertFalse(result['ok'])

    def test_missing_password_cannot_sign_in(self):
        self.assertFalse(self.box.security_command({'action':'owner_login'},1,Sensors())['ok'])

    def test_password_creates_short_session(self):
        result=self.login()
        self.assertTrue(result['ok'])
        self.assertTrue(self.box.security.authorized(result['token'],300))
        self.assertFalse(self.box.security.authorized(result['token'],301))

    def test_immediate_repeat_sign_in_replaces_old_session(self):
        first=self.login()['token']
        second=self.login(now=2)['token']
        self.assertFalse(self.box.security.authorized(first,2))
        self.assertTrue(self.box.security.authorized(second,2))

    def test_password_sign_in_works_immediately_after_restart(self):
        self.login()
        self.assertTrue(self.login(box=self.restart(),now=6)['ok'])

    def test_malformed_passwords_are_rejected(self):
        for password in (None,123,[],{},'x'*257):
            with self.subTest(password_type=type(password).__name__):
                result=self.box.security_command({'action':'owner_login','password':password},1,Sensors())
                self.assertFalse(result['ok'])

    def test_owner_failures_pause_and_survive_restart(self):
        for i in range(5):
            self.box.security_command({'action':'owner_login','password':'wrong'},i,Sensors())
        box=self.restart()
        self.assertFalse(self.login(box=box,now=6)['ok'])
        self.assertTrue(self.login(box=box,now=65)['ok'])

    def test_unauthenticated_issuance_rejected(self):
        self.assertFalse(self.issue('not-an-owner')['ok'])

    def test_eight_digit_code_is_not_in_saved_or_public_state(self):
        result=self.issue(self.login()['token'])
        self.assertTrue(result['ok'])
        self.assertEqual(len(result['code']),8)
        self.assertNotIn(result['code'],self.path.read_text())
        public=json.dumps(self.box.status(2,Sensors()))
        self.assertNotIn(result['code'],public)
        self.assertNotIn(CREDENTIAL_KEY,public)
        self.assertNotIn(PASSWORD,public)

    def test_code_expires_at_exact_deadline(self):
        result=self.issue(self.login()['token'],ttl=30)
        self.assertFalse(self.box.request_access(result['code'],32,Sensors(),'expired','courier'))
        self.assertEqual(self.box.history[-1]['detail'],'code expired')

    def test_code_role_is_enforced_without_consuming_it(self):
        result=self.issue(self.login()['token'])
        self.assertFalse(self.box.request_access(result['code'],3,Sensors(),'wrong-role','owner'))
        self.assertTrue(self.box.request_access(result['code'],4,Sensors(),'right-role','courier'))

    def test_single_use_code_cannot_unlock_twice(self):
        result=self.issue(self.login()['token'])
        self.assertTrue(self.box.request_access(result['code'],3,Sensors(),'first','courier'))
        self.box.request_close(4);self.box.tick(4,Sensors())
        self.assertFalse(self.box.request_access(result['code'],5,Sensors(),'second','courier'))
        self.assertEqual(self.box.history[-1]['detail'],'code already used')

    def test_revoked_code_is_denied(self):
        token=self.login()['token'];result=self.issue(token)
        self.assertTrue(self.box.security_command({'action':'revoke_code','token':token,'credential_id':result['id']},3,Sensors())['ok'])
        self.assertFalse(self.box.request_access(result['code'],4,Sensors(),'revoked','courier'))
        self.assertEqual(self.box.history[-1]['detail'],'code revoked')

    def test_unauthenticated_revocation_cannot_change_code(self):
        result=self.issue(self.login()['token'])
        self.assertFalse(self.box.security_command({'action':'revoke_code','token':'bad','credential_id':result['id']},3,Sensors())['ok'])
        self.assertTrue(self.box.request_access(result['code'],4,Sensors(),'still-valid','courier'))

    def test_fixed_demo_pins_are_disabled(self):
        self.assertFalse(self.box.request_access('2468',1,Sensors(),'legacy-courier','courier'))
        self.assertFalse(self.box.request_access('1357',2,Sensors(),'legacy-owner','owner'))

    def test_invalid_lifetimes_are_rejected(self):
        token=self.login()['token']
        for ttl in (True,0,29,3601,float('nan'),float('inf'),'300'):
            self.assertFalse(self.issue(token,ttl=ttl)['ok'])

    def test_new_code_supports_next_cycle_without_reset(self):
        token=self.login()['token'];first=self.issue(token)
        self.box.request_access(first['code'],3,Sensors(),'first','courier')
        self.box.request_close(4);self.box.tick(4,Sensors())
        second=self.issue(token,now=5)
        self.assertNotEqual(first['code'],second['code'])
        self.assertTrue(self.box.request_access(second['code'],6,Sensors(),'second','courier'))

    def test_tamper_revokes_all_codes_and_owner_session(self):
        token=self.login()['token'];first=self.issue(token);self.issue(token,role='owner')
        self.box.tick(3,Sensors(impact=True))
        self.assertTrue(self.box.security.lockdown)
        self.assertTrue(all(c['revoked'] for c in self.box.security.credentials))
        self.assertFalse(self.issue(token,now=4)['ok'])
        self.assertFalse(self.box.request_access(first['code'],4,Sensors(),'locked','courier'))

    def test_severe_impact_during_access_enters_lockdown(self):
        token=self.login()['token'];code=self.issue(token)
        self.box.request_access(code['code'],3,Sensors(),'open','courier')
        self.box.tick(4,Sensors(door_open=True,latch_locked=False,severe_impact=True))
        self.assertTrue(self.box.security.lockdown)
        self.assertIsNone(self.box.grant)

    def test_lockdown_and_revocation_survive_restart(self):
        self.issue(self.login()['token']);self.box.tick(3,Sensors(impact=True))
        box=self.restart()
        self.assertTrue(box.security.lockdown)
        self.assertTrue(all(c['revoked'] for c in box.security.credentials))

    def test_restart_invalidates_owner_session_but_keeps_unconsumed_code(self):
        token=self.login()['token'];result=self.issue(token)
        box=self.restart();box.tick(5.1,Sensors())
        self.assertFalse(self.issue(token,now=6,box=box)['ok'])
        self.assertTrue(box.request_access(result['code'],7,Sensors(),'after-restart','courier'))

    def test_clearing_lockdown_requires_new_password_session(self):
        token=self.login()['token'];self.box.tick(3,Sensors(impact=True))
        denied=self.box.security_command({'action':'clear_lockdown','token':token},4,Sensors())
        self.assertFalse(denied['ok'])
        fresh=self.login(now=5)['token']
        self.assertTrue(self.box.security_command({'action':'clear_lockdown','token':fresh},6,Sensors())['ok'])
        self.assertFalse(self.box.security.lockdown)

    def test_clearing_lockdown_requires_measured_secure_state(self):
        self.login();self.box.tick(3,Sensors(impact=True))
        token=self.login(now=4)['token']
        result=self.box.security_command({'action':'clear_lockdown','token':token},5,Sensors(door_open=True,latch_locked=False))
        self.assertFalse(result['ok'])
        self.assertTrue(self.box.security.lockdown)

    def test_clearing_lockdown_does_not_reactivate_revoked_codes(self):
        token=self.login()['token'];issued=self.issue(token);self.box.tick(3,Sensors(impact=True))
        token=self.login(now=4)['token']
        self.box.security_command({'action':'clear_lockdown','token':token},5,Sensors())
        self.assertFalse(self.box.request_access(issued['code'],6,Sensors(),'old','courier'))
        self.assertEqual(self.box.history[-1]['detail'],'code revoked')

    def test_code_use_and_revocation_remain_saved(self):
        token=self.login()['token'];first=self.issue(token);second=self.issue(token)
        self.box.request_access(first['code'],3,Sensors(),'used','courier')
        self.box.security_command({'action':'revoke_code','token':token,'credential_id':second['id']},4,Sensors())
        box=self.restart();box.tick(5.1,Sensors())
        self.assertFalse(box.request_access(first['code'],6,Sensors(),'used-again','courier'))
        self.assertFalse(box.request_access(second['code'],7,Sensors(),'revoked-again','courier'))

    def test_write_failure_does_not_return_issued_secret(self):
        token=self.login()['token']
        with patch.object(self.box.store,'save',side_effect=OSError('disk full')):
            result=self.issue(token)
        self.assertFalse(result['ok'])
        self.assertNotIn('code',result)
        self.assertTrue(self.box.storage_fault)

    def test_old_checkpoint_migrates_without_losing_pending_events(self):
        from lockbox.storage import StateStore
        old=Lockbox(auto_ack=False);event=old._event('tamper',1)
        state=old._state();state.pop('security_state')
        StateStore(self.path).save(state,1)
        box=self.restart(2)
        self.assertFalse(box.storage_fault)
        self.assertTrue(box.security.enabled)
        self.assertIn(event,box.pending)

    def test_legacy_authenticator_checkpoint_upgrades_without_losing_codes(self):
        from lockbox.storage import StateStore
        token=self.login()['token']
        issued=self.issue(token)
        state=self.box._state()
        security=state['security_state']
        security['version']=1
        security['totp_secret']=base64.b32encode(bytes.fromhex(security.pop('credential_key'))).decode()
        security['last_otp_counter']=123456
        StateStore(self.path).save(state,3)
        box=self.restart(4);box.tick(4.1,Sensors())
        self.assertFalse(box.storage_fault)
        self.assertTrue(self.login(box=box,now=5)['ok'])
        self.assertTrue(box.request_access(issued['code'],6,Sensors(),'migrated-code','courier'))
        saved=json.loads(self.path.read_text())['payload']['state']['security_state']
        self.assertEqual(saved['version'],2)
        self.assertNotIn('totp_secret',saved)
        self.assertNotIn('last_otp_counter',saved)


if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report={'passed':result.wasSuccessful(),'tests_run':result.testsRun,
            'failures':[str(test) for test,_ in result.failures],
            'errors':[str(test) for test,_ in result.errors],
            'method':'Password-only owner sessions, adversarial access cases and old-checkpoint migration'}
    (ROOT/'results/security_layers.json').write_text(json.dumps(report,indent=2)+'\n')
    raise SystemExit(0 if report['passed'] else 1)
