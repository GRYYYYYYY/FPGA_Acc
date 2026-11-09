"""Independent Bellman-Ford oracle for capped bounds on cyclic graphs."""
import sys,random,json,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from remaining_delay_halfns_cache_v3 import RemainingDelayCache
from pre_route_endpoints import sha
rng=random.Random(20261007)
with tempfile.TemporaryDirectory() as directory:
 out=Path(directory)
 for trial in range(100):
  n=8;edges=[(u,v,rng.randrange(0,8)) for u in range(n) for v in range(n) if u!=v and rng.random()<.22];offs=[0];dst=[];weights=[]
  for u in range(n):
   for a,b,w in edges:
    if a==u:dst.append(b);weights.append(w)
   offs.append(len(dst))
  class RC:
   scale=8*10**9
   increments=weights
   def initial(self,n):return 0
  f=dict(node_ids=list(range(n)),row_offsets=offs,dest_ranks=dst,edge_ids=list(range(len(dst))),capacities=[1]*n)
  work=out/str(trial);work.mkdir();g=work/'g';g.write_text(str(edges));c=RemainingDelayCache(g,sha(g),f,RC(),work/'bounds')
  for sink in range(n):
   h=c.get(sink);d=[float('inf')]*n;d[sink]=0
   for _ in range(n):
    for u,v,w in edges:d[u]=min(d[u],w+d[v])
   assert [h.get(u) for u in range(n)]==[min(x,4) for x in d]
   assert all(h.get(u)<=w+h.get(v) for u,v,w in edges)
receipt=R/'experiments/halfns_cache_contract_v3_2026-10-07/reproducible_receipt.json'
receipt.write_text(json.dumps(dict(trials=100,sinks=800,seed=20261007,cyclic_zero_weight_graphs=True,exact_capped_oracle_pass=True,bellman_pass=True,bindings={str(Path(__file__)):sha(__file__),str(R/'tools/remaining_delay_halfns_cache_v3.py'):sha(R/'tools/remaining_delay_halfns_cache_v3.py')}))+'\n');print('PASS 800 sinks')
