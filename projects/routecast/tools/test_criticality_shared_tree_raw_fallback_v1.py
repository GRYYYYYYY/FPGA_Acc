"""All-simple-path feasibility oracle, separate raw/objective reconstructions."""
import json,random
from pathlib import Path
from fractions import Fraction
from criticality_shared_tree_raw_fallback_v1 import Tree
from pre_route_endpoints import sha
rng=random.Random(301141);queries=0;fallbacks=0;accepted=0;infeasible=0
for trial in range(260):
 n=rng.randrange(3,8);off=[0];dst=[];inc=[]
 for u in range(n):
  for v in range(n):
   if u!=v and rng.random()<.38:dst.append(v);inc.append(rng.randrange(9))
  off.append(len(dst))
 initial=[rng.randrange(4) for _ in range(n)];tree=Tree(dict(row_offsets=off,dest_ranks=dst),inc,initial,0)
 for _ in range(12):
  target=rng.randrange(n);crit=rng.choice([Fraction(0),Fraction(1),Fraction(3,8),Fraction(13439003,33554432)]);prices=[rng.randrange(15) for _ in range(n)];budget=rng.randrange(20);old=dict(tree.arrival);oldparents=dict(tree.parents);p,q=crit.numerator,crit.denominator
  paths=[]
  def dfs(u,seen,raw,price):
   if u==target:paths.append((raw,p*raw+(q-p)*price));return
   for slot in range(off[u],off[u+1]):
    v=dst[slot]
    if v not in seen and v not in old:dfs(v,seen|{v},raw+inc[slot],price+prices[v])
  for u,raw in old.items():dfs(u,{u},raw,0)
  feasible=[x for x in paths if x[0]<=budget]
  result=tree.expand(target,crit,prices,budget);queries+=1
  assert result['committed']==bool(feasible)
  if result['used_raw_fallback']:
   fallbacks+=1
   assert result['raw']==min(raw for raw,_ in paths)
  if result['committed']:
   accepted+=1;assert tree.arrival[target]<=budget
   u=target;seen=set();raw=initial[0];newprice=0
   while u!=0:
    assert u not in seen;seen.add(u)
    if u not in old:newprice+=prices[u]
    a,slot=tree.parents[u];assert off[a]<=slot<off[a+1] and dst[slot]==u;raw+=inc[slot];u=a
   assert raw==tree.arrival[target]==result['raw']
   assert result['objective_numerator']==p*raw+(q-p)*newprice
   if not result['used_raw_fallback']:assert result['objective_numerator']==min(score for _,score in paths)
   assert all(tree.parents[k]==v for k,v in oldparents.items()) and all(tree.arrival[k]==v for k,v in old.items())
  else:
   infeasible+=1;assert tree.arrival==old and tree.parents==oldparents
# Previous turn's concrete counterexample is now accepted via raw 2.
t=Tree(dict(row_offsets=[0,2,3,4,4],dest_ranks=[1,2,3,3]),[5,1,5,1],[0]*4,0)
r=t.expand(3,Fraction(1,4),[0,0,100,0],3)
assert r['used_raw_fallback'] and r['committed'] and r['raw']==2 and r['objective_numerator']==302
out=Path('experiments/criticality_shared_tree_raw_fallback_contract_v1_2026-10-10');out.mkdir()
files=[Path(__file__).resolve(),Path(__file__).with_name('criticality_shared_tree_raw_fallback_v1.py').resolve(),Path(__file__).with_name('criticality_shared_tree_reference_v1.py').resolve()]
(out/'verification.json').write_text(json.dumps(dict(bindings={str(p):sha(p) for p in files},graphs=260,queries=queries,raw_fallbacks=fallbacks,accepted=accepted,infeasible=infeasible,independent_exhaustive_fixed_tree_feasibility_pass=True,scope='Fixed-tree extension feasibility only. Whole-NET reroute/backtracking and previous joint fallback not implemented here; no native/MMC/performance claims.'),indent=2)+'\n')
print('RAW FALLBACK CONTRACT PASS',queries,fallbacks,accepted,infeasible)
