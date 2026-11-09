"""Independent adjacency/full-search comparison with early-stop shared CSR."""
import pathlib,json,hashlib,random
from shortest_NET_tree_ensemble_v1 import prepare
from shortest_NET_tree_csr_certified_v2 import prepare_csr
R=pathlib.Path(__file__).resolve().parents[1]
def main():
 rng=random.Random(1019);passed=unreachable=0
 for case in range(300):
  n=7;kinds=['SOURCE']+['CHANX']*4+['SINK']*2;caps=[1]*n;raw=[(rng.randrange(n),rng.randrange(n),rng.randrange(4)) for _ in range(20)];raw.sort();edges=[(i,*e) for i,e in enumerate(raw)];offsets=[0]*(n+1)
  for _,u,_,_ in edges:offsets[u+1]+=1
  for i in range(n):offsets[i+1]+=offsets[i]
  dest=[v for _,_,v,_ in edges];costs=[c for _,_,_,c in edges];filtered=[(eid,u,v,c) for eid,u,v,c in edges if kinds[u]!='SINK' and kinds[v]!='SOURCE'];sinks=[5,6]
  try:reference=prepare(filtered,0,sinks)
  except ValueError:
   try:prepare_csr(offsets,dest,costs,caps,kinds,0,sinks)
   except ValueError:unreachable+=1;continue
   raise AssertionError('unreachable disagreement')
  actual=prepare_csr(offsets,dest,costs,caps,kinds,0,sinks)
  for key in ['source','sinks','choices','distance']:assert actual[key]==reference[key],(case,key)
  pc,ph=actual['potential_cost'],actual['potential_hops']
  assert (pc[0],ph[0])==(0,0)
  for eid,u,v,c in filtered:assert (pc[v],ph[v])<=(pc[u]+c,ph[u]+1)
  for sink in sinks:assert (pc[sink],ph[sink])==reference['distance'][sink]
  passed+=1
 O=R/'experiments/shortest_NET_tree_csr_certified_core_v2_2026-10-19';O.mkdir();files=[pathlib.Path(__file__).resolve(),R/'tools/shortest_NET_tree_csr_certified_v2.py',R/'tools/shortest_NET_tree_ensemble_v1.py'];v=dict(status='300_random_graph_early_stop_and_full_search_supports_match',bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},reachable_cases=passed,unreachable_cases=unreachable,seed=1019,scope='Core equivalence only; no real-graph performance/forecast claim.')
 with (O/'verification.json').open('x') as f:json.dump(v,f,indent=2);f.write('\n')
 print('PASS',passed,'reachable',unreachable,'unreachable')
if __name__=='__main__':main()
