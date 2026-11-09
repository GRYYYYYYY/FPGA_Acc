"""Authenticate complete heap-reuse model state and all feedback events."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
name=sys.argv[1];assert name in ('8051','xtea','mmc')
old=R/'experiments/freecores_resident_v1_2026-10-08'/name/'resident' if name!='mmc' else R/'experiments/ultraembedded_mmc_resident_v1_2026-10-08/mmc/resident'
new=R/'experiments/freecores_resident_reused_heap_v2_2026-10-08'/name if name!='mmc' else R/'experiments/ultraembedded_mmc_resident_reused_heap_v2_2026-10-08/mmc'
bindings={str(Path(__file__)):sha(Path(__file__))}
def auth(obj):
 if isinstance(obj,dict):
  for k,v in obj.items():
   if k in ('bindings','files') and isinstance(v,dict):
    for p,h in v.items():assert sha(p)==h,p
   else:auth(v)
 elif isinstance(obj,list):
  for v in obj:auth(v)
for folder in (old,new):
 p=folder/'receipt.json';d=json.loads(p.read_text());auth(d);bindings[str(p)]=sha(p)
for filename in ('floors.json','initial.json','round0.json','round1.json','sketch.json'):
 a=old/filename;b=new/filename;assert a.read_bytes()==b.read_bytes(),filename
 for p in (a,b):bindings[str(p)]=sha(p)
a=json.loads((old/'receipt.json').read_text());b=json.loads((new/'receipt.json').read_text());assert len(a['rounds'])==len(b['rounds'])==2
for ra,rb in zip(a['rounds'],b['rounds']):
 assert set(ra)==set(rb)
 for key in ra:
  if key not in ('seconds','state_file'):assert ra[key]==rb[key],key
result=dict(bindings=bindings,name=name,all_five_complete_state_files_byte_equal=True,all_feedback_events_price_schedule_epoch_and_outcome_equal=True,scope='Complete two-round state/events equivalence, authenticated separate producers. Concurrent candidate trials are not paired performance evidence; independent physical and event audit remains separate.')
assert all(sha(p)==h for p,h in bindings.items())
(new/'parity_verification.json').write_text(json.dumps(result,indent=2)+'\n');print(name,'full states and feedback events exact PASS')
