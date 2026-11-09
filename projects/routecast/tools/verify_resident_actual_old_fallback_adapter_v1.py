"""Synthetic CSR adapter contracts with independent path/union oracle."""
import copy,hashlib,json
from pathlib import Path
from resident_actual_old_fallback_adapter_v1 import fallback
f=dict(row_offsets=[0,2,3,4,6,6,6],dest_ranks=[1,2,3,3,4,5],edge_ids=[100,101,102,103,104,105],capacities=[1]*6)
slots={e:i for i,e in enumerate(f['edge_ids'])};increments=[1]*6
class RC:
 def initial(self,source):return 2
 def increment(self,slot):return increments[slot]
 def path(self,source,sink,path):return 2+sum(increments[slots[e]] for e in path)
qs=[dict(connection_id=i,net_id=7,source=0,sink=s) for i,s in ((9,4),(10,5))]
old=[dict(q,budget_integer=5,floor_integer=4,answer=dict(status='FOUND',physical_edge_ids=[100,102,104 if q['sink']==4 else 105],delay=5)) for q in qs]
parents={2:(0,1),3:(2,3),4:(3,4),5:(3,5)};prices={1:10};rc=RC();checks={}
for name,settled,cap,expect in [('full',{4,5},100,'ACCEPT_STRICT_IMPROVEMENT'),('partial',{4},100,'RETAIN'),('none',set(),100,'RETAIN'),('limit',{4,5},1,'RETAIN')]:
 before=copy.deepcopy((f,qs,old,parents,prices));a=fallback(f,rc,slots,qs,old,parents,settled,prices,1,cap)
 assert a['status']==expect and a['chosen_union_cost']<=a['old_union_cost'] and (f,qs,old,parents,prices)==before
 assert {r['connection_id'] for r in a['records']}=={9,10}
 union=set();incoming={}
 for r in a['records']:
  u=0;raw=2
  for e in r['answer']['physical_edge_ids']:
   slot=slots[e];assert f['row_offsets'][u]<=slot<f['row_offsets'][u+1]
   v=f['dest_ranks'][slot];assert v not in incoming or incoming[v]==e
   incoming[v]=e;union.add(e);raw+=increments[slot];u=v
  assert u==r['sink'] and raw==r['answer']['delay']<=5 and r['floor_integer']==4
 cost=2+sum(increments[slots[e]]+prices.get(f['dest_ranks'][slots[e]],0) for e in union)
 assert cost==a['chosen_union_cost']
 checks[name]=True
increments[1]=9
a=fallback(f,rc,slots,qs,old,parents,{4,5},prices,1);assert a['status']=='RETAIN';checks['over_budget_attempt_retained']=True
root=Path(__file__).resolve().parents[1];out=root/'experiments/resident_actual_old_fallback_adapter_v1_2026-10-09';out.mkdir(exist_ok=False)
files=[Path(__file__)]+[root/'tools'/n for n in ('resident_actual_old_fallback_adapter_v1.py','budget_actual_old_acceptance_v1.py','budget_joint_candidates_incremental_v2.py','budget_NET_gate_reference_v1.py')]
r=dict(all_pass=True,checks=checks,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},scope='Synthetic CSR adapter only. Independent original XML/Fraction online feedback audit, epoch/ledger integration and quality/time gains remain required.')
(out/'verification.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
