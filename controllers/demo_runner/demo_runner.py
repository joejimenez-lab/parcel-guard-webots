import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from lockbox.recording import record
schedule={
75:('access',{'code':'2468','role':'courier','request_id':'demo-courier'}),
180:('parcel_in',{'animate':True}),275:('close',{}),
415:('access',{'code':'2468','role':'courier','request_id':'demo-reuse'}),
525:('access',{'code':'1357','role':'owner','request_id':'demo-owner'}),
640:('parcel_out',{'animate':True}),750:('close',{})}
chapters=[
{'at':0,'title':'Empty box','description':'Sensors confirm the closed door and locked bolt.'},
{'at':2.14,'title':'Courier access','description':'Code 2468 retracts the bolt, then opens the door.'},
{'at':5.50,'title':'Parcel placement','description':'The script places the parcel. Delivery stays pending until the box locks.'},
{'at':8.55,'title':'Closing and locking','description':'Door and bolt feedback confirm delivery.'},
{'at':13.02,'title':'Used courier code','description':'A second request with code 2468 is denied.'},
{'at':16.54,'title':'Owner access','description':'Code 1357 opens the box for collection.'},
{'at':20.22,'title':'Parcel removal','description':'The script removes the parcel. The sensor change records retrieval.'},
{'at':23.74,'title':'Empty box after collection','description':'The door closes and the bolt locks. Both codes have now been used.'}]
def verify(rows):
 s=rows[-1]['status'];k=s['event_kinds']
 return {'delivery_once':k.count('delivery')==1,'retrieval_once':k.count('retrieval')==1,
         'used_code_denied':any(e['detail']=='courier code already used' for e in s['all_events']),
         'no_tamper_false_alarm':'tamper' not in k,'final_empty_and_secured':s['secured'] and s['parcel']=='empty',
         'delivery_only_when_secured':all(row['status']['secured'] for row in rows if any(e['kind']=='delivery' and e['time']>=row['status']['time']-.1 for e in row['status']['all_events'])),
         'every_event_acknowledged':s['pending']==0 and len(s['endpoint_ids'])==len(s['all_events'])}
record('workflow',900,schedule,chapters,verify)
