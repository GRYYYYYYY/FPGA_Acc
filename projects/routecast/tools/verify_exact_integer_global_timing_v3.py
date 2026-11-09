"""Independent full Fraction recurrences after fixed random DAG updates."""
import json,random
from fractions import Fraction as F
from pathlib import Path
from exact_integer_global_timing_v3 import ExactGlobalTiming
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/exact_integer_global_timing_v3_2026-10-08';D.mkdir(exist_ok=False)
rng=random.Random(20261008);updates=0;checks=0;noops=0
for case in range(100):
 n=20;edges={};mapping={};groups={};delays={i:F(rng.randrange(11),10) for i in range(5)}
 for u in range(n):
  for v in range(u+1,n):
   if rng.random()>.12:continue
   eid=str(len(edges));edges[eid]=dict(source=u,sink=v,disabled=False,max_delay_seconds=str(F(rng.randrange(-5,11),10)))
   if rng.random()<.65:
    groups[eid]=rng.randrange(5);mapping[eid]=dict(old_local_offset_seconds=str(F(rng.randrange(-5,6),10)))
 tg=dict(nodes={str(i):'SINK' if i in (n-1,n-3) else 'OTHER' for i in range(n)},edges=edges)
 allocation=dict(edge_connection_ids=groups);model=ExactGlobalTiming(tg,dict(external_edges=mapping),allocation,10,F(10000),delays)
 def verify():
  global checks
  weights={eid:F(mapping[eid]['old_local_offset_seconds'])+delays[groups[eid]] if eid in groups else F(e['max_delay_seconds']) for eid,e in edges.items()}
  forward={i:F(0) for i in range(n)}
  for v in range(n):
   forward[v]=max([F(0)]+[forward[e['source']]+weights[eid] for eid,e in edges.items() if e['sink']==v])
  back={i:F(0) if i in (n-1,n-3) else None for i in range(n)}
  for u in reversed(range(n)):
   candidates=([F(0)] if u in (n-1,n-3) else [])+[weights[eid]+back[e['sink']] for eid,e in edges.items() if e['source']==u and back[e['sink']] is not None]
   back[u]=max(candidates) if candidates else None
  assert {eid:F(v,model.scale) for eid,v in model.weights.items()}==weights
  assert {i:F(v,model.scale) for i,v in model.forward.items()}==forward
  assert {i:None if v is None else F(v,model.scale) for i,v in model.back.items()}==back
  assert model.cpd_seconds()==max(forward[n-1],forward[n-3]);checks+=1
 verify()
 for step in range(30):
  cid=step%5;value=delays[cid] if step%7==0 else F(rng.randrange(21),10)
  delays[cid]=value;model.update(cid,value);verify();updates+=1
  if model.update_work[-1]['changed_edges']==0:noops+=1
report=dict(graphs=100,updates=updates,full_fraction_vector_comparisons=checks,no_op_updates=noops,bindings={str(p):sha(p) for p in (Path(__file__),R/'tools/exact_integer_global_timing_v1.py',R/'tools/exact_integer_global_timing_v2.py',R/'tools/exact_integer_global_timing_v3.py')},scope='Fixed DAG exact affected propagation, signed offsets, increases/decreases, repeated query groups, disconnected nodes and no-op updates. Independent Fraction full recurrence, not native STA or HDL equivalence.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',report['updates'],'updates;',checks,'complete Fraction vectors')
