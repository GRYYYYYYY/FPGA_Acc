"""Sparse touched-price workspace versus full-vector reference and snapshots."""
import random,json
from pathlib import Path
from fractions import Fraction
from criticality_shared_tree_reference_v1 import Tree
from criticality_shared_tree_sparse_reference_v1 import Graph
from pre_route_endpoints import sha
rng=random.Random(583103);queries=0
for trial in range(160):
 n=rng.randrange(3,10);off=[0];dst=[];inc=[]
 for u in range(n):
  for v in range(n):
   if u!=v and rng.random()<.3:dst.append(v);inc.append(rng.randrange(9))
  off.append(len(dst))
 initial=[rng.randrange(4) for _ in range(n)];fields=dict(row_offsets=off,dest_ranks=dst);graph=Graph(fields,inc,initial)
 a=graph.tree(0);b=Tree(fields,inc,initial,0);separate=graph.tree(0)
 # Caller graph mutation after preparation must not change costs/identities.
 if dst:dst[0]=(dst[0]+1)%n
 inc[:]=[100]*len(inc);initial[:]=[100]*n
 for _ in range(15):
  prices={u:rng.randrange(12) for u in range(n)};crit=rng.choice([Fraction(0),Fraction(1),Fraction(3,8)]);target=rng.randrange(n);budget=rng.randrange(20)
  x=a.expand(target,crit,prices,budget);y=b.expand(target,crit,[prices[u] for u in range(n)],budget)
  assert x==y and a.arrival==b.arrival and a.parents==b.parents;queries+=1
 assert separate.arrival=={0:b.initial[0]} and separate.parents=={}
 assert a.offsets is separate.offsets and a.inc is separate.inc
out=Path('experiments/criticality_shared_tree_sparse_contract_v1_2026-10-10');out.mkdir()
files=[Path(__file__).resolve()]+[Path('tools')/x for x in ['criticality_shared_tree_sparse_reference_v1.py','criticality_shared_tree_reference_v1.py']]
(out/'verification.json').write_text(json.dumps(dict(bindings={str(p.resolve()):sha(p) for p in files},graphs=160,queries=queries,full_vector_reference_path_and_cost_equality=True,caller_mutation_and_tree_isolation_pass=True,scope='Sparse prices validated at touched destinations; untouched prices not inspected. Serial stable getter required. Python reference, no native or MMC performance claim.'),indent=2)+'\n');print('SPARSE CRITICALITY TREE CONTRACT PASS',queries)
