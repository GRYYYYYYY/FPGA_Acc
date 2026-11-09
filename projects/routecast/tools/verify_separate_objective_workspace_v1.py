"""Independent Python heap oracle; compare every observable output cell."""
import json,sys,heapq,random
from pathlib import Path
from types import SimpleNamespace
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from separate_objective_workspace_bridge_v1 import Search
from pre_route_endpoints import sha
rng=random.Random(1040811);none=(1<<64)-1;checked=0
binary=R/'experiments/separate_objective_workspace_build_v1_2026-10-08/search.so'
for graph in range(200):
 n=rng.randrange(3,20);row=[0];dest=[];rawinc=[];objective=[]
 for u in range(n):
  for v in range(n):
   if u!=v and rng.random()<0.25:
    dest.append(v);rawinc.append(rng.randrange(15));objective.append(rng.randrange(8))
  row.append(len(dest))
 cap=[int(rng.random()>0.1) for _ in range(n)]
 fields=dict(row_offsets=row,dest_ranks=dest,capacities=cap,edge_ids=list(range(len(dest))))
 initials=[rng.randrange(5) for _ in range(n)]
 rc=SimpleNamespace(increments=rawinc,initial=lambda u:initials[u])
 search=Search(fields,rc,binary,objective)
 for trial in range(12):
  src=rng.randrange(n);targets={rng.randrange(n) for _ in range(4)};prices={u:rng.randrange(5) for u in range(n)};weight=2 if trial<11 else 1<<62
  search.prepare(prices,weight);raw,parents,settled=search.search(src,targets)
  cost={src:initials[src]};expected_raw=[none]*n;pn=[none]*n;pe=[none]*n;done=[0]*n
  expected_raw[src]=initials[src];queue=[(initials[src],src)];remaining=set(targets)
  while queue and remaining:
   value,u=heapq.heappop(queue)
   if value!=cost[u]:continue
   if not done[u]:done[u]=1;remaining.discard(u)
   for e in range(row[u],row[u+1]):
    v=dest[e]
    if not cap[v]:continue
    candidate=value+objective[e]+weight*prices[v]
    if candidate<cost.get(v,1<<120):
     cost[v]=candidate;expected_raw[v]=expected_raw[u]+rawinc[e];pn[v]=u;pe[v]=e;heapq.heappush(queue,(candidate,v))
  assert list(raw)==expected_raw and list(search.pn)==pn and list(search.pe)==pe and list(search.settled)==done
  assert settled=={u for u in targets if done[u]};checked+=1
 search.close()
out=R/'experiments/separate_objective_workspace_contract_v1_2026-10-08';out.mkdir()
files=[Path(__file__),R/'tools/separate_objective_workspace_bridge_v1.py',R/'tools/soft_demand_cpp/separate_objective_workspace_v1.cpp',R/'tools/soft_demand_cpp_bridge_v1.py',binary]
(out/'verification.json').write_text(json.dumps(dict(bindings={str(p):sha(p) for p in files},random_graphs=200,sequential_searches=checked,all_raw_parent_node_edge_and_settled_arrays_exact_oracle_pass=True,scope='Objective and raw increments independent, sparse reuse and wide price tested. No complete RR ablation or physical delay/prediction proof.'),indent=2)+'\n')
print('PASS separate objective workspace',checked)
