import copy,json
from pathlib import Path
from types import MappingProxyType
from tree_floor_pareto_affected_seed_v12 import SeedContext,EdgeSlotContext,predict
from tree_floor_pareto_edge_context_v8 import predict as old
f=MappingProxyType(dict(row_offsets=(0,2,3,4,4),dest_ranks=(1,2,3,3),edge_ids=(0,1,2,3),capacities=(2,2,2,2)))
class RC:
 scale=10**10;increments=(1,2,1,1);initials=(0,0,0,0);arcs=((0,1,1),(0,2,2),(1,3,1),(2,3,1))
 def initial(self,n):return self.initials[n]
 def path(self,s,t,edges):
  d=self.initial(s)
  for e in edges:u,v,w=self.arcs[e];assert u==s;s=v;d+=w
  assert s==t;return d
rc=RC();kw=dict(spans=[0]*4);q=dict(connection_id=1,net_id=10,source=0,sink=1);seed=old(f,rc,[q],{(0,1):1},**kw)['records'];seed[0]['meta']={'nested':[3]};ctx=SeedContext(f,rc,seed);before=copy.deepcopy(seed);edge=EdgeSlotContext(f)
for net in (10,20):
 query=[dict(connection_id=2,net_id=net,source=0,sink=3)]
 for forbidden in ({},{net:frozenset({1})}):
  kwargs=dict(kw,forbidden_by_net=forbidden,edge_context=edge);a=old(f,rc,query,{(0,3):2},seed_records=seed,**kwargs);b=predict(f,rc,query,{(0,3):2},seed_context=ctx,**kwargs);assert a==b
  b['records'][0]['meta']['nested'].append(8);b['records'][0]['answer']['physical_edge_ids'].clear();b['ledger'].clear();assert predict(f,rc,query,{(0,3):2},seed_context=ctx,**kwargs)==a
assert seed==before
original=rc.increments;rc.increments=tuple(list(original))
try:ctx.fork(f,rc,{10})
except ValueError:pass
else:raise AssertionError('changed RC accepted')
rc.increments=original
out=Path(__file__).resolve().parents[1]/'experiments/affected_seed_contract_v1_2026-10-07';out.mkdir();(out/'receipt.json').write_text(json.dumps(dict(existing_and_new_net_query_parity=True,forbidden_path_parity=True,nested_metadata_and_path_ledger_isolation=True,model_replacement_rejected=True,scope='Software fork contract, no general occupancy-dependent route reuse or native proof.'))+'\n');print('PASS affected seed contract')
