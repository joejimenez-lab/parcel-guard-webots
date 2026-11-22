"""End-to-end security workflow with independent physical device feedback."""
import json
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from lockbox.webots_harness import Harness

h=Harness()
replies=h.robot.getDevice('security_rx');replies.enable(h.dt)
checks={};snapshots={};error=None
password=os.environ.get('PARCEL_GUARD_OWNER_PASSWORD','owner-5650')
private_values=[]

def owner(action,**data):
    while replies.getQueueLength():replies.nextPacket()
    h.send(action,**data)
    for _ in range(80):
        h.step()
        if replies.getQueueLength():
            reply=json.loads(replies.getString());replies.nextPacket()
            for key in ('token','code'):
                if reply.get(key):private_values.append(reply[key])
            return reply
    raise RuntimeError(f'No private reply for {action}')

def access(code,role,request_id):
    h.send('access',code=code,role=role,request_id=request_id)
    h.require(lambda s:s['door_angle_rad']>=1 and s['latch']=='unlocked','Issued access code did not open the box')

def denied(code,role,request_id):
    h.send('access',code=code,role=role,request_id=request_id);h.advance(12)
    return h.latest['last_access_result'] is False and h.latest['grant']=='none'

def require_owner(result):
    if not result.get('ok'):raise RuntimeError(result.get('message','Owner command denied'))
    return result

try:
    h.advance(20);h.require(lambda s:s['secured'],'Security world did not initialize')
    checks['secure_default']={'enabled':h.latest['security']['enabled'],
        'fixed_courier_denied':denied('2468','courier','fixed-courier'),
        'fixed_owner_denied':denied('1357','owner','fixed-owner')}
    bad_password=owner('owner_login',password='wrong')
    missing_password=owner('owner_login')
    login=require_owner(owner('owner_login',password=password));old_token=login['token']
    login=require_owner(owner('owner_login',password=password));token=login['token']
    old_session_denied=not owner('issue_code',token=old_token,role='courier',ttl_s=300)['ok']
    checks['owner_password']={'wrong_password_denied':not bad_password['ok'],
        'missing_password_denied':not missing_password['ok'],'password_only_accepted':login['ok'],
        'immediate_repeat_sign_in_works':old_session_denied}
    revoked=require_owner(owner('issue_code',token=token,role='courier',ttl_s=300))
    revoked_result=owner('revoke_code',token=token,credential_id=revoked['id'])
    checks['revocation']={'owner_revocation_accepted':revoked_result['ok'],
        'revoked_code_denied':denied(revoked['code'],'courier','revoked-code')}
    # A successful authorized access clears the earlier credential-failure count.
    delivery=require_owner(owner('issue_code',token=token,role='courier',ttl_s=300))
    collection=require_owner(owner('issue_code',token=token,role='owner',ttl_s=300))
    access(delivery['code'],'courier','delivery-one');h.send('parcel_in');h.advance(15);h.close()
    delivery_done=h.latest['event_kinds'].count('delivery')==1 and h.latest['parcel']=='present'
    reuse_denied=denied(delivery['code'],'courier','used-code')
    access(collection['code'],'owner','collection-one');h.send('parcel_out');h.advance(15);h.close()
    checks['managed_delivery_cycle']={'delivery_confirmed':delivery_done,'reused_code_denied':reuse_denied,
        'collection_confirmed':h.latest['event_kinds'].count('retrieval')==1 and h.latest['parcel']=='empty'}
    original_session=h.latest['session']
    second=require_owner(owner('issue_code',token=token,role='courier',ttl_s=300))
    access(second['code'],'courier','delivery-two');h.send('parcel_in');h.advance(15);h.close()
    checks['repeat_delivery_without_reset']={'same_policy_session':h.latest['session']==original_session,
        'second_delivery_confirmed':h.latest['event_kinds'].count('delivery')==2}
    expiring=require_owner(owner('issue_code',token=token,role='owner',ttl_s=30))
    h.advance(960)
    checks['expiry']={'expired_code_denied':denied(expiring['code'],'owner','expired-code')}
    live=require_owner(owner('issue_code',token=token,role='owner',ttl_s=300))
    snapshots['protected']=h.latest
    h.send('impact')
    h.require(lambda s:s['security']['lockdown'],'Tamper did not trigger lockdown')
    h.require(lambda s:s['secured'],'Lockdown did not reach measured closure')
    snapshots['lockdown']=h.latest
    old_owner_denied=not owner('clear_lockdown',token=token)['ok']
    checks['incident_lockdown']={'all_codes_revoked':all(c['revoked'] for c in h.latest['security']['credentials']),
        'old_owner_session_invalidated':old_owner_denied,
        'previously_valid_code_blocked':denied(live['code'],'owner','lockdown-code'),
        'physical_box_secured':h.latest['secured']}
    h.send('reset_logic');h.advance(12)
    reset_blocked=h.latest['session']==original_session and h.latest['security']['lockdown']
    count=h.latest['recovery_count'];h.send('restart_controller')
    h.require(lambda s:s['recovery_count']>count,'Security controller did not restore')
    h.require(lambda s:s['secured'],'Recovered lockdown did not secure')
    checks['lockdown_restart']={'reset_cannot_bypass':reset_blocked,
        'lockdown_persisted':h.latest['security']['lockdown'],
        'revocations_persisted':all(c['revoked'] for c in h.latest['security']['credentials'])}
    login=require_owner(owner('owner_login',password=password))
    token=login['token']
    clear=require_owner(owner('clear_lockdown',token=token));h.advance(9)
    old_still_revoked=denied(live['code'],'owner','after-clear-old-code')
    fresh=require_owner(owner('issue_code',token=token,role='owner',ttl_s=300))
    access(fresh['code'],'owner','after-clear-owner');h.send('parcel_out');h.advance(15);h.close()
    checks['owner_recovery']={'password_sign_in_accepted':login['ok'],'lockdown_cleared':clear['ok'],
        'old_code_remains_revoked':old_still_revoked,'new_code_works':h.latest['parcel']=='empty' and h.latest['secured']}
    public=json.dumps(h.latest)
    checks['secret_redaction']={'no_password_in_status':password not in public,
        'no_private_reply_values_in_status':all(value not in public for value in private_values)}
    snapshots['recovered']=h.latest
except Exception as exc:
    error=str(exc)

h.finish({'passed':error is None and len(checks)==10 and all(all(group.values()) for group in checks.values()),
          'checks':checks,'runner_error':error,'snapshots':snapshots,'final_status':h.latest},'webots_security.json')
