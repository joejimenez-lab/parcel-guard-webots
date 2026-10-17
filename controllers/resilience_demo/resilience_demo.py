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
{'at':0,'title':'Access and fault tests','description':'Starting with an empty, locked box.'},
{'at':2.30,'title':'Wrong role','description':'Owner code 1357 cannot open the box as a courier.'},
{'at':6.78,'title':'Expired code','description':'For this test, the courier code expires after five seconds.'},
{'at':10.62,'title':'Link disconnected','description':'Local sensing continues.'},
{'at':12.38,'title':'Offline impact alerts','description':'Three impacts create three alerts. The queue holds them until reconnection.'},
{'at':18.62,'title':'Link restored','description':'The endpoint receives the queued events and returns acknowledgments.'},
{'at':21.98,'title':'Lost acknowledgments','description':'Three acknowledgments are dropped. Retried events count only once.'},
{'at':24.70,'title':'Owner access','description':'The bolt retracts before the door opens.'},
{'at':28.54,'title':'Blocked bolt','description':'Motor force is disabled and a brake holds the bolt retracted.'},
{'at':31.60,'title':'Locking fault','description':'The two-second timeout leaves the box marked unsecured.'},
{'at':35.26,'title':'Bolt released','description':'The fault clears after the position sensor confirms locking.'}]
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
