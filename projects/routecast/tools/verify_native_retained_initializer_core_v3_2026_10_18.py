"""Independent Python reference and fullNET fallback/rollback validation."""
import json,random,copy,sys
sys.path.insert(0,str(__import__('pathlib').Path(__file__).resolve().parent/'native_resume_prototype'))
from source_binding_v2 import closure
from compiled_criticality_tree_v1 import BINARY
from pathlib import Path
from fractions import Fraction
from compiled_criticality_tree_v1 import Graph
from criticality_shared_tree_sparse_reference_v3 import Graph as Reference
from retained_criticality_tree_seed_v1 import seed
from raw_retained_tree_expand_v1 import expand
from native_retained_net_initializer_v1 import initialize
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/native_retained_initializer_core_v3_2026-10-18';rng=random.Random(20261018);cases=0;nonminimum=0;rejections=0
for trial in range(200):
 n=14;edges={}
 for v in range(1,10):edges[0,v]=rng.randrange(1,25)
 for u in range(1,10):
  for v in range(u+1,14):
   if v>=10 or rng.random()<.25:edges[u,v]=rng.randrange(1,25)
 edges[1,2]=rng.randrange(1,25)
 row=[0];dest=[];inc=[];slots={}
 for u in range(n):
  for (a,b),w in sorted(edges.items()):
   if a==u:slots[a,b]=len(dest);dest.append(b);inc.append(w)
  row.append(len(dest))
 f=dict(row_offsets=row,dest_ranks=dest,edge_ids=list(range(len(dest))),capacities=[1]*n);initial=[rng.randrange(5)]*n
 g=Graph(f,inc,initial);ref=Reference(f,inc,initial);t=g.tree(0);rt=ref.tree(0);path=[slots[0,1],slots[1,2],slots[2,10]];arrival=initial[0]+sum(inc[s] for s in path)
 seed(t,[(10,path,arrival)]);seed(rt,[(10,path,arrival)])
 plain=ref.tree(0);minresult=plain.expand(10,Fraction(1),{},10**6);nonminimum+=arrival>minresult['raw']
 for target in [11,12,13]:
  budget=rng.choice([0,15,40,1000]);before=(dict(t.parents),dict(t.arrival));a=expand(t,target,budget);b=rt.expand(target,Fraction(1),{},budget);assert a==b and t.parents==rt.parents and t.arrival==rt.arrival
  if not a['committed']:assert before==(t.parents,t.arrival);rejections+=1
  cases+=1
 g.close()
# Deliberate seed-induced budget failure: retained node arrival10 vs direct3.
f=dict(row_offsets=[0,2,4,4,4],dest_ranks=[1,3,2,3],edge_ids=[0,1,2,3],capacities=[1,1,1,1]);inc=[10,3,1,10];g=Graph(f,inc,[0]*4);kinds=['SOURCE','CHANX','SINK','SINK']
old=[dict(connection_id=0,net_id=0,source=0,sink=2,answer=dict(status='FOUND',physical_edge_ids=[0,2],delay=11)),dict(connection_id=1,net_id=0,source=0,sink=2,answer=dict(status='FOUND',physical_edge_ids=[0,2],delay=11))]
queries=[dict(connection_id=0,net_id=0,source=0,sink=2),dict(connection_id=1,net_id=0,source=0,sink=3)];budgets={0:11,1:3};snapshot=copy.deepcopy(old);calls=[]
def fb():
 calls.append(1);return {0:dict(status='FOUND',physical_edge_ids=[0,2],delay=11),1:dict(status='FOUND',physical_edge_ids=[1],delay=3)}
a=initialize(g,f,kinds,queries,old,budgets,range(4),fb);assert not a['whole_NET_fallback'] and a['retained_connection_ids']==[0] and old==snapshot and not calls
# Lower budget below every feasible repair; fallback itself fails, no source mutation.
try:initialize(g,f,kinds,queries,old,{0:11,1:2},range(4),fb)
except ValueError:pass
else:raise AssertionError('bad fallback budget admitted')
assert old==snapshot and len(calls)==1
# Capacity-zero shortcut chosen by raw kernel must force wholeNET validated fallback.
g.close()
f2=dict(row_offsets=[0,3,5,5,5],dest_ranks=[1,2,3,2,3],edge_ids=list(range(5)),capacities=[1,0,1,1]);g2=Graph(f2,[1,4,9,1,1],[0]*4)
q=[queries[1]];o=[dict(connection_id=1,net_id=0,source=0,sink=2,answer=dict(status='FOUND',physical_edge_ids=[1],delay=4))]
a=initialize(g2,f2,kinds,q,o,{1:9},range(5),lambda:{1:dict(status='FOUND',physical_edge_ids=[2],delay=9)})
assert a['whole_NET_fallback'] and a['answers'][1]['physical_edge_ids']==[2]
g2.close()
f3=dict(row_offsets=[0,3,4,6,6,6,6],dest_ranks=[1,2,3,2,4,5],edge_ids=list(range(6)),capacities=[1]*6);g3=Graph(f3,[1,100,1,1,1,1],[0]*6)
q3=[dict(connection_id=0,net_id=0,source=0,sink=4),dict(connection_id=1,net_id=0,source=0,sink=5)]
o3=[dict(connection_id=0,net_id=0,source=0,sink=4,answer=dict(status='FOUND',physical_edge_ids=[1,4],delay=101)),dict(connection_id=1,net_id=0,source=0,sink=3,answer=dict(status='FOUND',physical_edge_ids=[2],delay=1))];before=copy.deepcopy(o3)
fallback3={0:dict(status='FOUND',physical_edge_ids=[0,3,4],delay=3),1:dict(status='FOUND',physical_edge_ids=[0,3,5],delay=3)}
a3=initialize(g3,f3,['SOURCE','CHANX','CHANX','SINK','SINK','SINK'],q3,o3,{0:101,1:4},range(6),lambda:fallback3)
assert a3['whole_NET_fallback'] and a3['fallback_reason']=='RETAIN_RAW_BUDGET' and a3['retained_connection_ids']==[] and a3['attempted_retained_connection_ids']==[0] and a3['answers']==fallback3 and o3==before
g3.close()
result=dict(status='pass',successful_whole_NET_budget_fallback=True,bindings={**closure([Path(__file__)]),str(BINARY):sha(BINARY)},random_graphs=200,independent_reference_expansions=cases,seed_nonminimum_arrival_graphs=nonminimum,budget_or_unreachable_rejections_without_tree_mutation=rejections,source_records_unchanged=True,invalid_fallback_rejected=True,disabled_resource_forces_physical_fallback=True,sources={str(R/'tools'/n):sha(R/'tools'/n) for n in ['raw_retained_tree_expand_v1.py','native_retained_net_initializer_v1.py','retained_criticality_tree_seed_v1.py','criticality_shared_tree_sparse_reference_v3.py']})
with (D/'verification.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps({k:v for k,v in result.items() if k not in ['bindings','sources']}),flush=True)
