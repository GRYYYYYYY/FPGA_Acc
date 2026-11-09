"""Independent Dijkstra exact floors for sequential multi-target A* prefixes."""
import hashlib,json,random,heapq
from pathlib import Path
from collections import Counter
from compiled_quotient_raw_floor_v1_2026_10_17 import tree
from compiled_quotient_criticality_astar_v1 import Graph,BINARY
from static_quotient_lower_bound_v1 import LowerBound
R=Path(__file__).resolve().parents[1];D=R/'experiments/quotient_raw_floor_contract_v1_2026-10-17';D.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
contract=R/'experiments/compiled_quotient_astar_contract_v1_2026-10-17/verification.json';proof=json.loads(contract.read_text());assert proof['all_pass'] and proof['bindings'][str(BINARY)]==sha(BINARY)
rng=random.Random(2026101701);calls=0;statuses=Counter();maxbits=0;rejected=0
for case in range(120):
 n=24;rows=[0];dest=[];inc=[];scale=1 if case%2 else 2**90+3
 for u in range(n):
  for v in range(n):
   if rng.random()<0.09:dest.append(v);inc.append(rng.randrange(8)*scale)
  rows.append(len(dest))
 fields=dict(row_offsets=rows,dest_ranks=dest,capacities=[1]*n);initial=[rng.randrange(5)*scale for _ in range(n)]
 lower=LowerBound(fields,inc,initial,[rng.randrange(9)*scale for _ in range(n)],[i//3 for i in range(n)],max_targets=8);g=Graph(lower)
 try:
  source=rng.randrange(n);t=tree(g,source);distance={source:initial[source]};queue=[(initial[source],source)]
  while queue:
   d,u=heapq.heappop(queue)
   if d!=distance[u]:continue
   for slot in range(rows[u],rows[u+1]):
    v=dest[slot];nd=d+inc[slot]
    if v not in distance or nd<distance[v]:distance[v]=nd;heapq.heappush(queue,(nd,v))
  targets=list(range(n));rng.shuffle(targets)
  for target in targets+targets[::-1]:
   before=(dict(t.arrival),dict(t.parents));answer=t.expand(target);calls+=1;statuses[answer['status']]+=1
   if target not in distance:
    assert answer['status']=='UNREACHABLE' and before==(t.arrival,t.parents);continue
   assert answer['status']=='COMMITTED' and answer['raw']==distance[target];maxbits=max(maxbits,answer['raw'].bit_length())
   u=source;seen={u};value=initial[source]
   for slot in answer['path_slots']:
    assert rows[u]<=slot<rows[u+1];u=dest[slot];assert u not in seen;seen.add(u);value+=inc[slot]
   assert u==target and value==distance[target]
   assert all(distance[v]==a for v,a in t.arrival.items())
   for v,(parent,slot) in t.parents.items():assert dest[slot]==v and t.arrival[parent]+inc[slot]==t.arrival[v]
  for target in [-1,n,True]:
   before=(dict(t.arrival),dict(t.parents))
   try:t.expand(target)
   except ValueError:rejected+=1
   else:raise AssertionError('invalid target accepted')
   assert before==(t.arrival,t.parents)
 finally:g.close()
assert calls==5760 and maxbits>90 and statuses['UNREACHABLE']>0 and rejected==360
files=[Path(__file__).resolve(),R/'tools/compiled_quotient_raw_floor_v1_2026_10_17.py',R/'tools/compiled_quotient_criticality_astar_v1.py',R/'tools/static_quotient_lower_bound_v1.py',contract,BINARY]
with (D/'verification.json').open('x') as f:json.dump(dict(bindings={str(p):sha(p) for p in files},all_pass=True,graphs=120,expansions=calls,status_counts=dict(statuses),invalid_target_refusals=rejected,maximum_floor_bits=maxbits,all_exact_Dijkstra_floors_paths_and_retained_prefixes_pass=True,scope='Random directed graphs include zero costs, cycles, unreachable targets, merged quotient groups and >90bit costs. Old Dijkstra equal-cost path parity is not asserted. No real-design performance or whole-model result.'),f,indent=2);f.write('\n')
print(dict(graphs=120,expansions=calls,status_counts=dict(statuses),invalid_target_refusals=rejected,maximum_floor_bits=maxbits))
