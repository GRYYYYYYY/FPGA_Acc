"""Independent exhaustive simple-path oracle on small directed graphs."""
import json,random
from pathlib import Path
from fractions import Fraction
from criticality_shared_tree_reference_v1 import Tree
from pre_route_endpoints import sha
rng=random.Random(217039);queries=0;commits=0;rejects=0;unreachable=0
for trial in range(240):
 n=rng.randrange(3,8);off=[0];dst=[];inc=[]
 for u in range(n):
  for v in range(n):
   if v!=u and rng.random()<.35:dst.append(v);inc.append(rng.randrange(0,9))
  off.append(len(dst))
 initial=[rng.randrange(4) for _ in range(n)];fields=dict(row_offsets=off,dest_ranks=dst);tree=Tree(fields,inc,initial,0)
 for i in range(12):
  target=rng.randrange(n);crit=rng.choice([Fraction(0),Fraction(1),Fraction(1,4),Fraction(7,8),Fraction(13439003,33554432)])
  congestion=[rng.randrange(10) for _ in range(n)];budget=rng.randrange(1,30);old=dict(tree.arrival);oldparents=dict(tree.parents);p,q=crit.numerator,crit.denominator
  scores=[]
  def walk(u,seen,raw,price):
   if u==target:scores.append(p*raw+(q-p)*price);return
   for slot in range(off[u],off[u+1]):
    v=dst[slot]
    if v in seen or v in old:continue
    walk(v,seen|{v},raw+inc[slot],price+congestion[v])
  for u,raw in old.items():walk(u,{u},raw,0)
  result=tree.expand(target,crit,congestion,budget);queries+=1
  if not scores:
   assert result['status']=='UNREACHABLE' and tree.arrival==old and tree.parents==oldparents;unreachable+=1;continue
  assert result['objective_numerator']==min(scores)
  if result['committed']:
   commits+=1;assert result['raw']<=budget and tree.arrival[target]==result['raw']
   assert all(tree.parents[k]==v for k,v in oldparents.items()) and all(tree.arrival[k]==v for k,v in old.items())
   for u,raw in tree.arrival.items():
    seen=set();v=u;total=initial[0]
    while v!=0:
     assert v not in seen;seen.add(v);a,slot=tree.parents[v];assert off[a]<=slot<off[a+1] and dst[slot]==v;total+=inc[slot];v=a
    assert total==raw
  else:
   rejects+=1;assert result['raw']>budget and tree.arrival==old and tree.parents==oldparents
# Shared branch reuse: new congestion charged once, old-tree raw arrival retained.
t=Tree(dict(row_offsets=[0,1,3,3,3],dest_ranks=[1,2,3]),[2,3,4],[0]*4,0)
a=t.expand(2,Fraction(1,2),[0,100,10,20],100);b=t.expand(3,Fraction(1,2),[0,100,10,20],100)
assert a['objective_numerator']==115 and b['objective_numerator']==26 and b['attach']==1 and b['new_nodes']==1 and b['raw']==6
out=Path('experiments/criticality_shared_tree_reference_contract_v1_2026-10-10');out.mkdir()
files=[Path(__file__).resolve(),Path(__file__).with_name('criticality_shared_tree_reference_v1.py').resolve()]
(out/'verification.json').write_text(json.dumps(dict(bindings={str(p):sha(p) for p in files},graphs=240,queries=queries,commits=commits,raw_budget_rejections=rejects,unreachable=unreachable,exhaustive_path_optimality_and_tree_raw_invariants=True,scope='Small-graph reference only; no native exactness, complete budget-feasible alternative search, full MMC or performance evidence.'),indent=2)+'\n')
print('CRITICALITY SHARED TREE CONTRACT PASS',queries,commits,rejects,unreachable)
