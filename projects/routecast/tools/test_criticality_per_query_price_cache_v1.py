"""Within-query price cache parity; no cross-query stale price reuse."""
import random,json
from pathlib import Path
from fractions import Fraction
from criticality_shared_tree_sparse_reference_v2 import Graph as Original
from criticality_shared_tree_sparse_reference_v3 import Graph as Cached
from pre_route_endpoints import sha
rng=random.Random(120921);before=after=queries=0
class Prices:
 def __init__(self,values):self.values=values;self.calls=0
 def get(self,u,default=0):self.calls+=1;return self.values[u]
for trial in range(160):
 n=rng.randrange(4,13);off=[0];dst=[];inc=[]
 for u in range(n):
  for v in range(n):
   if u!=v and rng.random()<.5:dst.append(v);inc.append(rng.randrange(7))
  off.append(len(dst))
 f=dict(row_offsets=off,dest_ranks=dst);initial=[0]*n;a=Original(f,inc,initial).tree(0);b=Cached(f,inc,initial).tree(0)
 for _ in range(12):
  # Prices change both upward/downward between calls, including after rejects.
  values=[rng.randrange(15) for _ in range(n)];x=Prices(values);y=Prices(values);target=rng.randrange(n);c=rng.choice([Fraction(0),Fraction(1),Fraction(7,8)]);budget=rng.randrange(20)
  ra=a.expand(target,c,x,budget);rb=b.expand(target,c,y,budget)
  assert ra==rb and a.parents==b.parents and a.arrival==b.arrival and y.calls<=x.calls
  before+=x.calls;after+=y.calls;queries+=1
assert before>after
out=Path('experiments/criticality_per_query_price_cache_contract_v1_2026-10-10');out.mkdir()
files=[Path(__file__).resolve()]+[Path('tools')/x for x in ['criticality_shared_tree_sparse_reference_v2.py','criticality_shared_tree_sparse_reference_v3.py']]
(out/'verification.json').write_text(json.dumps(dict(bindings={str(p.resolve()):sha(p) for p in files},graphs=160,queries=queries,original_price_gets=before,cached_price_gets=after,all_paths_parents_raw_objectives_equal=True,scope='Within-query stable price snapshot only; cache discarded on every call. Getter count is not elapsed speedup or full MMC evidence.'),indent=2)+'\n');print('PER QUERY PRICE CACHE PASS',queries,before,after)
