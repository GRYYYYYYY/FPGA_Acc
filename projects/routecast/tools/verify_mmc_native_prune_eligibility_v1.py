"""Independent root-down propagation versus producer sink-up walks."""
import json,sys
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
O=R/'experiments/mmc_selective_tree_preflight_v1_2026-10-13';p=O/'native_round1_eligibility_v1.json';v=json.loads(p.read_text());bindings={**v['bindings'],**closure([Path(__file__)]),str(p):sha(p)};assert all(sha(k)==h for k,h in bindings.items())
state=R/'experiments/mmc_native_iteration_state_observer_v2_2026-10-10/states/round_1.tsv';congested=set();children=defaultdict(lambda:defaultdict(list));roots={};pin_nodes=defaultdict(dict);sizes=Counter()
with state.open() as f:
 for line in f:
  a=line.split()
  if a[0]=='N' and int(a[2])>int(a[3]):congested.add(int(a[1]))
  elif a[0]=='T':
   net,n,parent=int(a[1]),int(a[2]),int(a[3]);sizes[net]+=1
   if parent==-1:assert net not in roots;roots[net]=n
   else:children[net][parent].append(n)
   if int(a[6])>=1:assert int(a[6]) not in pin_nodes[net];pin_nodes[net][int(a[6])]=n
queries=defaultdict(dict)
for line in (R/'experiments/native_manifest_scope_preflight_v1_2026-10-10/mmc.queries').read_text().splitlines():
 a=line.split()
 if a[0]=='Q':cid,net,pin,source,sink=map(int,a[1:]);assert pin not in queries[net];queries[net][pin]=(source,sink)
expected={r['net']:r for r in v['pernet']};assert set(expected)==set(queries)==set(roots);total=0
for net,qs in queries.items():
 root=roots[net];order=[];bad={root:root in congested};parents={};todo=[root]
 while todo:
  n=todo.pop();order.append(n)
  for child in children[net][n]:
   assert child not in bad;parents[child]=n;bad[child]=bad[n] or child in congested;todo.append(child)
 assert len(order)==sizes[net]
 clean_sinks=set()
 for pin,(source,sink) in qs.items():
  assert source==root and pin_nodes[net][pin]==sink
  if not bad[sink]:clean_sinks.add(sink)
 keep=set(clean_sinks)
 for n in reversed(order):
  if n in keep and n!=root:keep.add(parents[n])
 r=expected[net];assert r['clean_connections']==sum(not bad[sink] for source,sink in qs.values());assert r['congested_connections']==sum(bad[sink] for source,sink in qs.values());assert r['clean_union_nodes']==len(keep) and r['old_union_nodes']==len(order);total+=len(qs)
assert total==115572 and all(sha(k)==h for k,h in bindings.items());(O/'native_round1_eligibility_independent_verification_v1.json').write_text(json.dumps(dict(bindings=bindings,all_manifest_paths_root_down_congestion_and_retained_union_equal=True,connections=total,nets=len(queries),scope='Independent snapshot eligibility only; no force flags, nonconfigurable closure, online pruning or runtime savings proof.'),indent=2)+'\n');print('PASS root-down eligibility',total,len(queries),flush=True)
