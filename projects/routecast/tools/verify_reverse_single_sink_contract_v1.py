"""Independent forward Dijkstra validates reverse batched costs and paths."""
import heapq,json,random,sys
from pathlib import Path
from array import array
from types import SimpleNamespace
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from soft_demand_reverse_bridge_v1 import Reverse
B=R/'experiments/soft_demand_reverse_build_v1_2026-10-08/search.so'
bindings={**closure([Path(__file__)]),str(B):sha(B),str(R/'tools/soft_demand_cpp/tree_workspace_reverse_v1.cpp'):sha(R/'tools/soft_demand_cpp/tree_workspace_reverse_v1.cpp')}
def oracle(f,rc,source,sink,prices,weight):
 dist={source:rc.initial(source)};queue=[(dist[source],source)]
 while queue:
  cost,u=heapq.heappop(queue)
  if dist[u]!=cost:continue
  if u==sink:return cost
  for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   v=f['dest_ranks'][slot]
   if not f['capacities'][v]:continue
   candidate=cost+rc.increments[slot]+weight*prices.get(v,0)
   if candidate<dist.get(v,1<<120):dist[v]=candidate;heapq.heappush(queue,(candidate,v))
 return None
batches=queries=0
for seed in range(200):
 rng=random.Random(seed);n=rng.randint(4,30)
 f={k:array('Q') for k in ['row_offsets','dest_ranks','capacities']}
 f['capacities'].extend(rng.randrange(3) for _ in range(n));f['capacities'][0]=1
 f['row_offsets'].append(0);inc=[]
 for u in range(n):
  for v in range(n):
   if rng.random()<.15:
    f['dest_ranks'].append(v);inc.append(rng.randrange(7))
    if rng.random()<.15:f['dest_ranks'].append(v);inc.append(rng.randrange(7))
  f['row_offsets'].append(len(inc))
 rc=SimpleNamespace(increments=inc,initial=lambda node:node%5)
 search=Reverse(f,rc,B);enabled=[i for i in range(n) if f['capacities'][i]]
 for step in range(6):
  prices={i:(rng.randrange(8)+(1<<50 if step==5 else 0)) for i in range(n)}
  weight=[0,1,17,1<<63,0,1<<60][step]
  search.prepare(prices,weight);sink=rng.choice(enabled);sources=set(rng.sample(enabled,rng.randrange(len(enabled)+1)))
  result=search.batch(sink,sources);assert set(result)==sources
  for source,answer in result.items():
   expected=oracle(f,rc,source,sink,prices,weight)
   if expected is None:assert answer is None
   else:
    assert answer is not None;u=source;seen={u};raw=rc.initial(source);cost=raw
    for slot in answer['slots']:
     assert f['row_offsets'][u]<=slot<f['row_offsets'][u+1]
     u=f['dest_ranks'][slot];assert u not in seen and f['capacities'][u]>0;seen.add(u)
     raw+=inc[slot];cost+=inc[slot]+weight*prices.get(u,0)
    assert u==sink and raw==answer['raw'] and cost==answer['objective']==expected
   queries+=1
  snapshot=[list(getattr(search,k)) for k in ['raw','pn','pe','settled']]
  try:search.batch(sink,{n})
  except RuntimeError:pass
  else:raise AssertionError('invalid source accepted')
  assert snapshot==[list(getattr(search,k)) for k in ['raw','pn','pe','settled']]
  batches+=1
 search.close()
assert all(sha(p)==h for p,h in bindings.items())
D=R/'experiments/reverse_single_sink_contract_v1_2026-10-08';D.mkdir(exist_ok=False)
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,random_graphs=200,batches=batches,source_sink_queries=queries,independent_forward_minimum_objectives_and_returned_physical_paths_pass=True,scope='Positive-capacity query terminals; directed parallel/zero-cost arcs, disabled internal nodes, unreachable/source-equals-sink/empty batches, changing prices and >64bit objectives. Equal-cost paths can differ. No full real-design/model/native/performance proof.'),indent=2)+'\n')
print('PASS reverse batches',batches,'source queries',queries)
