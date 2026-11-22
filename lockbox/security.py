"""Password owner sign-in, revocable credentials and persistent lockdown."""
import base64
import hashlib
import hmac
import json
import math
import secrets



class SecurityPolicy:
    def __init__(self, enabled=False, password='owner-5650', credential_key=None, state=None):
        self.enabled = enabled
        self.credential_key = credential_key or secrets.token_hex(32)
        self.salt = secrets.token_hex(16)
        self.password_hash = self._password(password) if enabled else ''
        self.owner_failures = 0
        self.owner_paused_until = 0.0
        self.lockdown = False
        self.incident = ''
        self.credentials = []
        self.sessions = {}
        if state is not None:
            self.restore(state)

    def _password(self, password):
        return hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(self.salt), 200000).hex()

    def _digest(self, code):
        return hmac.new(bytes.fromhex(self.credential_key), code.encode(), hashlib.sha256).hexdigest()

    def snapshot(self):
        return json.loads(json.dumps({
            'version': 2, 'enabled': self.enabled, 'credential_key': self.credential_key,
            'password_salt': self.salt, 'password_hash': self.password_hash,
            'owner_failures': self.owner_failures,
            'owner_paused_until': self.owner_paused_until, 'lockdown': self.lockdown,
            'incident': self.incident, 'credentials': self.credentials,
        }))

    def restore(self, state):
        # Preserve the old digest key and all credential/incident state when
        # upgrading a checkpoint created by the former authenticator workflow.
        if isinstance(state, dict) and state.get('version') == 1:
            try:
                state = {**state, 'version': 2,
                         'credential_key': base64.b32decode(state['totp_secret']).hex()}
                del state['totp_secret']
                del state['last_otp_counter']
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError('invalid legacy security checkpoint') from exc
        if (not isinstance(state, dict) or set(state) != set(self.snapshot()) or state['version'] != 2
                or type(state['enabled']) is not bool or type(state['lockdown']) is not bool
                or not isinstance(state['incident'], str) or len(state['incident']) > 256
                or type(state['owner_failures']) is not int or not 0 <= state['owner_failures'] < 5
                or type(state['owner_paused_until']) not in (float, int)
                or not math.isfinite(state['owner_paused_until']) or state['owner_paused_until'] < 0
                or not isinstance(state['credentials'], list) or len(state['credentials']) > 128):
            raise ValueError('invalid security checkpoint')
        try:
            if len(bytes.fromhex(state['credential_key'])) < 20 or len(bytes.fromhex(state['password_salt'])) != 16:
                raise ValueError('invalid secret length')
            if state['enabled'] and len(bytes.fromhex(state['password_hash'])) != 32:
                raise ValueError('invalid password verifier')
            ids = set()
            for credential in state['credentials']:
                if (set(credential) != {'id', 'role', 'digest', 'expires', 'used', 'revoked'}
                        or not isinstance(credential['id'], str) or credential['id'] in ids
                        or credential['role'] not in ('courier', 'owner')
                        or len(bytes.fromhex(credential['digest'])) != 32
                        or type(credential['used']) is not bool or type(credential['revoked']) is not bool
                        or type(credential['expires']) not in (float, int)
                        or not math.isfinite(credential['expires']) or credential['expires'] < 0):
                    raise ValueError('invalid credential record')
                ids.add(credential['id'])
        except (TypeError, KeyError, AttributeError) as exc:
            raise ValueError('invalid security secrets') from exc
        # Enabling the interactive security mode cannot be undone by an older
        # checkpoint created in the legacy evaluation mode.
        if state['enabled']:
            self.enabled = True
            self.credential_key, self.salt = state['credential_key'], state['password_salt']
            self.password_hash = state['password_hash']
            self.owner_failures, self.owner_paused_until = state['owner_failures'], state['owner_paused_until']
            self.lockdown, self.incident = state['lockdown'], state['incident']
            self.credentials = json.loads(json.dumps(state['credentials']))

    def login(self, password, now):
        if not self.enabled or now < self.owner_paused_until:
            return {'ok': False, 'message': 'Owner sign-in is paused or unavailable.'}
        password_ok = (isinstance(password, str) and len(password) <= 256
                       and hmac.compare_digest(self._password(password), self.password_hash))
        if not password_ok:
            self.owner_failures += 1
            if self.owner_failures >= 5:
                self.owner_paused_until, self.owner_failures = now + 60, 0
            return {'ok': False, 'message': 'Owner sign-in denied. Check the owner password.'}
        self.owner_failures = 0
        # Signing in again immediately is allowed and invalidates the old session.
        token = secrets.token_urlsafe(32)
        self.sessions = {token: now + 300}
        return {'ok': True, 'token': token, 'expires': now + 300, 'message': 'Owner signed in.'}

    def authorized(self, token, now):
        return isinstance(token, str) and now < self.sessions.get(token, -1)

    def issue(self, token, role, ttl, now):
        if not self.authorized(token, now):
            return {'ok': False, 'message': 'Sign in as owner first.'}
        if self.lockdown:
            return {'ok': False, 'message': 'Clear the security lockdown before issuing a code.'}
        if (role not in ('owner', 'courier') or type(ttl) not in (float, int)
                or not math.isfinite(ttl) or not 30 <= ttl <= 3600):
            return {'ok': False, 'message': 'Choose a role and a lifetime from 30 to 3600 seconds.'}
        if len(self.credentials) >= 128:
            return {'ok': False, 'message': 'Credential history is full; archive this demonstration before provisioning more.'}
        # Keep every issued code distinct in this policy session, even after use.
        while True:
            code = str(secrets.randbelow(10 ** 8)).zfill(8)
            digest = self._digest(code)
            if all(c['digest'] != digest for c in self.credentials):
                break
        credential = {'id': secrets.token_hex(6), 'role': role, 'digest': digest,
                      'expires': now + ttl, 'used': False, 'revoked': False}
        self.credentials.append(credential)
        return {'ok': True, 'code': code, 'id': credential['id'], 'role': role,
                'expires': credential['expires'], 'message': 'One-use code created. Copy it now; it will not appear in the event log.'}

    def match(self, code, now):
        if not isinstance(code, str) or len(code) > 128:
            return None, 'invalid code'
        digest = self._digest(code)
        for credential in self.credentials:
            if hmac.compare_digest(credential['digest'], digest):
                if credential['revoked']:
                    return None, 'code revoked'
                if credential['used']:
                    return None, 'code already used'
                if now >= credential['expires']:
                    return None, 'code expired'
                return credential, ''
        return None, 'invalid code'

    def revoke(self, token, credential_id, now):
        if not self.authorized(token, now):
            return {'ok': False, 'message': 'Sign in as owner first.'}
        for credential in self.credentials:
            if credential['id'] == credential_id:
                credential['revoked'] = True
                return {'ok': True, 'message': 'Code revoked.', 'id': credential_id}
        return {'ok': False, 'message': 'Code was not found.'}

    def enter_lockdown(self, reason):
        if self.enabled:
            self.lockdown = True
            self.incident = reason[:256]
            self.sessions.clear()
            for credential in self.credentials:
                credential['revoked'] = True

    def public(self, now):
        return {'enabled': self.enabled, 'lockdown': self.lockdown, 'incident': self.incident,
                'owner_paused_s': max(0, round(self.owner_paused_until - now, 1)),
                'credentials': [{key: c[key] for key in ('id', 'role', 'expires', 'used', 'revoked')}
                                for c in self.credentials[-16:]]}
