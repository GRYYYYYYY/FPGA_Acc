"""Adversarial full-array parity for zero-cost ordering and 120-bit frontier."""
import json,sys
from pathlib import Path
from array import array
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from soft_demand_cpp_bridge_v1 import Search as Original
from soft_demand_workspace_bridge_v1 import Search as Candidate
old=R/'experiments/soft_demand_cpp_build_v1_2026-10-07/search.so';new=R/'experiments/soft_demand_workspace_radix_build_v3_2026-10-08/search.so';prior=R/'experiments/soft_demand_workspace_radix_contract_v3_2026-10-08/verification.json';p=json.loads(prior.read_text());assert p['sequential_searches_full_raw_parent_edge_and_settled_arrays_equal']==2400 and all(sha(k)==h for k,h in p['bindings'].items())
bindings={**closure([Path(__file__)]),str(old):sha(old),str(new):sha(new),str(prior):sha(prior),str(R/'tools/soft_demand_cpp/tree_workspace_radix_v3.cpp'):sha(R/'tools/soft_demand_cpp/tree_workspace_radix_v3.cpp')}
fixtures=[('backward_zero_cycle',8,[(u,v,0) for u in range(8) for v in range(8) if u!=v]),('stale_parallel_relaxations',8,[(7,6,9),(7,6,8),(7,6,1),(7,5,0),(5,6,0),(6,4,0),(4,5,0),(4,3,1),(3,2,0),(2,1,0),(1,0,0)]),('wide_raw_and_price',8,[(u,v,(1<<58)+(u+v)%3) for u in range(8) for v in range(8) if u!=v]),('disconnected_zero_capacity',8,[(u,(u+1)%8,0) for u in range(8)])]
checked=0
for name,n,edges in fixtures:
 f={k:array('Q') for k in ('row_offsets','dest_ranks','capacities')};f['capacities'].extend(0 if name=='disconnected_zero_capacity' and u==4 else 1 for u in range(n));f['row_offsets'].append(0);inc=[]
 for u in range(n):
  for x,v,w in edges:
   if x==u:f['dest_ranks'].append(v);inc.append(w)
  f['row_offsets'].append(len(inc))
 class RC:
  increments=inc
  def initial(self,node):return 0
 a=Original(f,RC(),old);b=Candidate(f,RC(),new)
 for step in range(24):
  src=[7,0,6,3][step%4];targets=[{0,1},{7},{4},set(),set(range(n)),{src}][step%6]
  prices={} if step%3==0 else {u:((1<<55)+(u%3)*(1<<54)) if step%3==1 else u%2 for u in range(n)};weight=1<<60 if step%3==1 else 1
  a.prepare(prices,weight);b.prepare(prices,weight);a.search(src,targets);b.search(src,targets)
  for field in ('raw','pn','pe','settled'):assert list(getattr(a,field))==list(getattr(b,field)),(name,step,field)
  checked+=1
 b.close()
assert checked==96 and all(sha(k)==h for k,h in bindings.items())
out=R/'experiments/soft_demand_workspace_radix_adversarial_v4_2026-10-08';out.mkdir();(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,adversarial_queries=checked,full_raw_parent_node_edge_and_settled_arrays_equal=True,coverage=['Backward zero-cost cycles and lower-node-ID insertions at last cost','Parallel and stale queued relaxation items','Frontier weighted prices above 2^115 and raw increments2^58','Empty targets, source targets, unreachable zero-capacity targets, consecutive resets'],scope='Random2400 plus crafted96 all-array differential, not real full-model/physical/native or speed proof.'),indent=2)+'\n');print('Radix96 adversarial + frozen2400 random full arrays PASS')
