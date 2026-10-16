import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from lockbox.recording import record
schedule={
30:('reset_logic',{'courier_ttl_s':5}),
80:('access',{'code':'1357','role':'courier','request_id':'wrong-role'}),
220:('access',{'code':'2468','role':'courier','request_id':'expired'}),
260:('reset_logic',{}),340:('link_off',{}),
395:('impact',{}),450:('impact',{}),505:('impact',{}),590:('link_on',{}),
660:('drop_acks',{'count':3}),695:('impact',{}),
780:('access',{'code':'1357','role':'owner','request_id':'fault-owner'}),
855:('jam_latch',{}),900:('close',{}),1110:('release_latch',{})}
chapters=[
{'at':0,'title':'Security under pressure','description':'A second walkthrough tests denied access, offline alerts and a blocked bolt.'},
{'at':2.30,'title':'Wrong role rejected','description':'An owner code cannot be used for a courier request.'},
{'at':6.78,'title':'Expired token rejected','description':'The controller checks expiry using simulated time.'},
{'at':10.62,'title':'The message link goes offline','description':'Event detection continues while outbound delivery is paused.'},
{'at':12.38,'title':'Three impacts. Three alerts.','description':'Each detected impact gets an ID and remains in the outbox.'},
{'at':18.62,'title':'Recovery without duplicates','description':'The simulated endpoint acknowledges every queued event ID once.'},
{'at':21.98,'title':'A lost ACK triggers retry','description':'Duplicate packets are deduplicated by the endpoint.'},
{'at':24.70,'title':'Approved access opens the box','description':'Measured bolt travel is confirmed before the door moves.'},
{'at':28.54,'title':'The bolt is physically disabled','description':'Available motor force is set to zero while the locking target remains commanded.'},
{'at':31.60,'title':'Fault. Never falsely secured.','description':'A two-second timeout exposes the failed bolt position.'},
{'at':35.26,'title':'Measured recovery','description':'Force is restored. The fault clears only after the bolt reaches its target.'}]
def verify(rows):
 all_events=[e for row in rows for e in row['status']['events']]
 final=rows[-1]['status']
 return {'wrong_role_denied':any(e['detail']=='code does not match requested role' for e in all_events),
         'expired_denied':any(e['detail']=='expired courier code' for e in all_events),
         'offline_queue_reaches_4':any(row['status']['link']=='offline' and row['status']['pending']>=4 for row in rows),
         'three_offline_impacts':sum(e['kind']=='tamper' and e['detail']=='impact detected' for e in final['all_events'])==4,
         'queue_drained':final['pending']==0,'acks_retried':final['endpoint_duplicate_packets']>=3,
         'blocked_bolt_fault':any(row['status']['phase']=='FAULT' and not row['status']['secured'] for row in rows),
         'recovery_confirmed':final['secured'] and 'latch_recovered' in final['event_kinds']}
record('resilience',1400,schedule,chapters,verify)
