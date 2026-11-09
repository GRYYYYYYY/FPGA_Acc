import json
from pathlib import Path
from tree_floor_pareto_edge_context_v8 import predict,EdgeSlotContext
from tree_floor_pareto_constraints_predictor_v7 import predict as old
f=dict(row_offsets=(0,2,3,4,4),dest_ranks=(1,2,3,3),edge_ids=(0,1,2,3),capacities=(2,2,2,2))
class RC:
 scale=10**10;increments=(1,2,1,1)
 def initial(self,n):return 0
 def path(self,s,t,edges):
  d=0
  for e in edges:assert f['row_offsets'][s]<=e<f['row_offsets'][s+1];s=f['dest_ranks'][e];d+=self.increments[e]
  assert s==t;return d
rc=RC();c=EdgeSlotContext(f);q=[dict(connection_id=7,net_id=23,source=0,sink=3)];kw=dict(spans=[0]*4)
a=old(f,rc,q,{(0,3):2},**kw);b=predict(f,rc,q,{(0,3):2},edge_context=c,**kw);assert a==b
assert predict(f,rc,[],{},seed_records=a['records'],edge_context=c,**kw)==old(f,rc,[],{},seed_records=a['records'],**kw)
try:c.slots(dict(f,edge_ids=tuple(list(f['edge_ids']))))
except ValueError:pass
else:raise AssertionError('replacement accepted')
try:c.slots(f)[0]=99
except TypeError:pass
else:raise AssertionError('mutable map')
for ids in ([0,1],(1,1)):
 try:EdgeSlotContext(dict(f,edge_ids=ids))
 except ValueError:pass
 else:raise AssertionError('invalid context accepted')
out=Path(__file__).resolve().parents[1]/'experiments/edge_slot_context_contract_v1_2026-10-07';out.mkdir();(out/'receipt.json').write_text(json.dumps(dict(search_and_seed_parity=True,replacement_rejected=True,immutable_map=True,invalid_snapshots_rejected=True,scope='Small software context contract, not native/full-cohort proof.'))+'\n');print('PASS edge context')
