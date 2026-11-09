import json,random,sys
from pathlib import Path
from array import array
R=Path.cwd();sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from soft_demand_cpp_bridge_v1 import Search as Original
from soft_demand_workspace_stats_bridge_v4 import Search as Candidate
out=R/'experiments/soft_demand_workspace_radix_stats_contract_v4_2026-10-08';out.mkdir();binary=R/'experiments/soft_demand_workspace_radix_stats_build_v4_2026-10-08/search.so';oldbinary=R/'experiments/soft_demand_cpp_build_v1_2026-10-07/search.so';bindings={**closure([Path(__file__)]),str(binary):sha(binary),str(oldbinary):sha(oldbinary),str(R/'tools/soft_demand_cpp/tree_workspace_radix_stats_v4.cpp'):sha(R/'tools/soft_demand_cpp/tree_workspace_radix_stats_v4.cpp')};calls=0
for seed in range(200):
 rng=random.Random(seed);n=rng.randint(3,30);f={k:array('Q') for k in ['row_offsets','dest_ranks','capacities']};f['capacities'].extend(rng.randrange(3) for _ in range(n));f['row_offsets'].append(0);inc=[]
 for u in range(n):
  for v in range(n):
   if rng.random()<.15 or v==(u+1)%n:f['dest_ranks'].append(v);inc.append(rng.randrange(6));
  f['row_offsets'].append(len(inc))
 class RC:
  increments=inc
  def initial(self,node):return node%5
 rc=RC();a=Original(f,rc,oldbinary);b=Candidate(f,rc,binary)
 for step in range(12):
  prices={i:rng.randrange(8) for i in range(n)};weight=[0,1,17,1<<63][step%4];a.prepare(prices,weight);b.prepare(prices,weight);src=rng.randrange(n);targets=set(rng.sample(range(n),rng.randrange(n+1)))
  x=a.search(src,targets);y=b.search(src,targets);assert x[2]==y[2]
  for field in ['raw','pn','pe','settled']:assert list(getattr(a,field))==list(getattr(b,field)),(seed,step,field)
  metric=b.metrics[-1];assert metric['settled']==sum(b.settled) and metric['pushes']==metric['relaxations']+1 and metric['pops']<=metric['pushes'] and metric['stale']<=metric['pops'] and metric['settled']<=metric['touched']<=n
  calls+=1
  # Invalid targets must leave output arrays untouched and allow the next query.
  snapshots={field:list(getattr(b,field)) for field in ['raw','pn','pe','settled']}
  try:b.search(src,{n})
  except RuntimeError:pass
  else:raise AssertionError('invalid target accepted')
  assert all(list(getattr(b,field))==value for field,value in snapshots.items())
 b.close()
assert calls==2400 and all(sha(k)==v for k,v in bindings.items());(out/'verification.json').write_text(json.dumps({'bindings':bindings,'random_graphs':200,'sequential_searches_full_raw_parent_edge_and_settled_arrays_equal':calls,'invalid_target_preservation_and_recovery_checks':calls,'wide_weights_over_64_bits_included':True,'scope':'Differential to frozen original 120-bit kernel, all node arrays, consecutive queries including empty target sets/zero cost/capacity/changed prices; real full model parity still required.'},indent=2)+'\n');print(calls)
