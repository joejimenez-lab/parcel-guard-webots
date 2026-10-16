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
{'at':0,'title':'Ready for delivery','description':'Door closed. Bolt position confirms the box is secured.'},
{'at':2.14,'title':'One-use courier access','description':'The role-bound code retracts the bolt before the door opens.'},
{'at':5.50,'title':'A parcel arrives','description':'The distance array confirms presence across three stable samples.'},
{'at':8.55,'title':'Delivery secured','description':'Door feedback and bolt feedback must both reach their targets.'},
{'at':13.02,'title':'A used code is rejected','description':'The courier token has already been redeemed.'},
{'at':16.54,'title':'Owner retrieval','description':'An owner code authorizes collection of the parcel.'},
{'at':20.22,'title':'Retrieval detected','description':'The parcel leaves the sensor array during approved access.'},
{'at':23.74,'title':'Ready for the next delivery','description':'The door closes and the measured bolt position confirms locking.'}]
def verify(rows):
 s=rows[-1]['status'];k=s['event_kinds']
 return {'delivery_once':k.count('delivery')==1,'retrieval_once':k.count('retrieval')==1,
         'used_code_denied':any(e['detail']=='courier code already used' for e in s['all_events']),
         'no_tamper_false_alarm':'tamper' not in k,'final_empty_and_secured':s['secured'] and s['parcel']=='empty',
         'every_event_acknowledged':s['pending']==0 and len(s['endpoint_ids'])==len(s['all_events'])}
record('workflow',1000,schedule,chapters,verify)
