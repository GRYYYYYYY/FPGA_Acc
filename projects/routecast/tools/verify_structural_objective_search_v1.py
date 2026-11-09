"""Independent weighted Dijkstra and complete parent/path audit, sequential calls."""
from pathlib import Path
from types import SimpleNamespace
from collections import Counter
import random,heapq,json
from pre_route_endpoints import sha
from structural_objective_search_v1 import Search
R=Path(__file__).resolve().parents[1];O=R/'experiments/structural_objective_contract_v1_2026-10-10';O.mkdir(exist_ok=True);binary=R/'experiments/soft_demand_workspace_radix_build_v3_2026-10-08/search.so';counts=Counter();witness=None
for seed in range(200):
 rng=random.Random(seed);n=rng.randrange(5,36);f=dict(row_offsets=[0],dest_ranks=[],capacities=[1]*n,edge_ids=[]);inc=[]
 for u in range(n):
  for v in range(n):
   if rng.random()<.15 or v==(u+1)%n:f['dest_ranks'].append(v);inc.append(rng.choice([0,0,1,5,2**40]));f['edge_ids'].append(len(inc)-1)
  f['row_offsets'].append(len(inc))
 rc=SimpleNamespace(increments=inc,initial=lambda u:u%7);base=[rng.choice([0,1,4,17]) for _ in range(n)];s=Search(f,rc,binary,base)
 for step in range(12):
  src=rng.randrange(n);targets=set(rng.sample(range(n),rng.randrange(2,5)));prices={u:rng.randrange(8) for u in range(n)};weight=[0,1,17,2**63][step%4];enabled=step%3!=0;s.prepare(prices,weight,structural=enabled)
  d={src:src%7};q=[(d[src],src)]
  while q:
   cost,u=heapq.heappop(q)
   if cost!=d[u]:continue
   for e in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    v=f['dest_ranks'][e]
    if not f['capacities'][v]:continue
    new=cost+inc[e]+(base[v] if enabled else 0)+weight*prices[v]
    if new<d.get(v,2**200):d[v]=new;heapq.heappush(q,(new,v))
  raw,parent,found=s.search(src,targets);assert found==targets&d.keys()
  for t in sorted(found):
   u=t;seen={u};path=[]
   while u!=src:
    prev,e=parent[u];assert f['row_offsets'][prev]<=e<f['row_offsets'][prev+1] and f['dest_ranks'][e]==u;assert prev not in seen;seen.add(prev);path.append(e);u=prev
   delay=src%7+sum(inc[e] for e in path);objective=delay+sum(weight*prices[f['dest_ranks'][e]]+(base[f['dest_ranks'][e]] if enabled else 0) for e in path);assert raw[t]==delay and objective==d[t]==s.last_objectives[t];counts['paths']+=1
  # Restore through a rejected preparation and exercise the next real search.
  try:s.prepare({0:-1},weight)
  except ValueError:pass
  else:raise AssertionError('negative price accepted')
  counts['queries']+=1
 s.close()
 try:s.search(0,{1,2})
 except RuntimeError:counts['closed_rejections']+=1
 else:raise AssertionError('closed result accepted')

# A structural optimum must return raw RC, not the optimization cost.
f=dict(row_offsets=[0,2,3,3],dest_ranks=[2,1,2],edge_ids=[0,1,2],capacities=[1,1,1])
rc=SimpleNamespace(increments=[1,0,0],initial=lambda u:0);base=[0,100,0]
a=Search(f,rc,binary,base)
try:a.search(0,{2})
except RuntimeError:pass
else:raise AssertionError('unprepared search accepted')
base[1]=0;rc.increments[0]=99
# Input snapshots preserve the original direct-edge raw cost of one.
a.prepare({},0,structural=False);raw,_,_=a.search(0,{2});assert raw[2]==0
a.prepare({},0,structural=True);raw,parent,found=a.search(0,{2});assert raw[2]==1 and parent[2]==(0,0) and a.last_objectives[2]==1
try:a.prepare({1:-1},0)
except ValueError:pass
else:raise AssertionError('invalid prepare accepted')
assert a.search(0,{2})[0][2]==1
assert a.search(0,set())==({}, {}, set())
a.close()
import sys
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
bindings={**closure([Path(__file__)]),str(binary):sha(binary),str(R/'experiments/bidirectional_rc_build_v2_2026-10-08/search.so'):sha(R/'experiments/bidirectional_rc_build_v2_2026-10-08/search.so')}
(O/'verification.json').write_text(json.dumps(dict(bindings=bindings,graphs=200,counts=dict(counts),all_raw_and_independent_minimum_structural_objectives_pass=True,scope='Random prototype: explicit floor mode excludes static cost; enabled mode selects structural objective but returns original RC raw. Not real graph/native base mapping/full feedback or performance.'),indent=2)+'\n')
print('STRUCTURAL OBJECTIVE CONTRACT PASS',counts)
