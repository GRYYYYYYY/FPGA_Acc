"""Scaled integer search and budget decisions versus independent Fraction shortest paths."""
import heapq,json,random
from pathlib import Path
from fractions import Fraction
from scaled_frozen_present_prices_v1 import Prices
from criticality_shared_tree_sparse_reference_v3 import Graph
from pre_route_endpoints import sha
rng=random.Random(20261011)
for trial in range(400):
 n=8;edges=[(u,v,rng.randrange(1,20)) for u in range(n) for v in range(u+1,n) if v==u+1 or rng.random()<.3]
 row=[0];dest=[];inc=[]
 for u in range(n):
  for a,b,w in edges:
   if a==u:dest.append(b);inc.append(w)
  row.append(len(dest))
 bases=[rng.randrange(1,40) for _ in range(n)];acc=[rng.randrange(1,8) for _ in range(n)];occ=[rng.randrange(6) for _ in range(n)];caps=[rng.randrange(1,4) for _ in range(n)];owned={i for i in range(n) if occ[i] and rng.random()<.5};pf=Fraction(rng.randrange(20),rng.randrange(1,12));c=Fraction(rng.randrange(1,9),10);budget=rng.randrange(8,100)
 prices=Prices(bases,acc,occ,caps,owned,pf);fields={'row_offsets':row,'dest_ranks':dest};g=Graph(fields,[prices.scale_raw(x) for x in inc],[0]*n);result=g.tree(0).expand(7,c,prices,prices.scale_raw(budget))
 distances={0:Fraction(0)};raw={0:0};queue=[(Fraction(0),0)]
 while queue:
  d,u=heapq.heappop(queue)
  if d!=distances[u]:continue
  for slot in range(row[u],row[u+1]):
   v=dest[slot];other=occ[v]-(1 if v in owned else 0)
   p=Fraction(bases[v]*acc[v])*(1+pf*max(0,other-caps[v]+1))
   candidate=d+c*inc[slot]+(1-c)*p
   if v not in distances or candidate<distances[v]:distances[v]=candidate;raw[v]=raw[u]+inc[slot];heapq.heappush(queue,(candidate,v))
 assert Fraction(result['objective_numerator'],result['objective_denominator']*prices.denominator)==distances[7]
 assert result['raw']==raw[7]*prices.denominator and result['committed']==(raw[7]<=budget)
 before=prices.get(3);occ[3]+=100;bases[3]+=100;assert prices.get(3)==before
R=Path(__file__).resolve().parents[1];O=R/'experiments/scaled_frozen_present_contract_v1_2026-10-10';O.mkdir();files=[Path(__file__),R/'tools/scaled_frozen_present_prices_v1.py',R/'tools/criticality_shared_tree_sparse_reference_v3.py']
(O/'verification.json').write_text(json.dumps({'bindings':{str(f.resolve()):sha(f) for f in files},'independent_shortest_path_graphs':400,'objective_raw_budget_decisions_pass':True,'snapshot_external_mutation_isolation_pass':True,'scope':'Small DAG exact objective/raw/budget scaling and immutable price snapshot only; no full native graph replay, native equivalence, affected schedule or QoR proof.'},indent=2)+'\n');print('SCALED FROZEN PRICES CONTRACT PASS')
