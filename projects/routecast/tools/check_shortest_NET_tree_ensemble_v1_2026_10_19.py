"""Exhaustive small-graph reference checks, no native labels or model fit."""
import pathlib,json,hashlib,itertools
from fractions import Fraction
from collections import Counter
from shortest_NET_tree_ensemble_v1 import prepare,materialize,sample
R=pathlib.Path(__file__).resolve().parents[1]
def simple_paths(edges,source,sink):
 adj={}
 for eid,u,v,c in edges:adj.setdefault(u,[]).append((v,c,eid))
 def walk(u,seen,path,cost):
  if u==sink:yield (cost,len(path)),tuple(path);return
  for v,c,eid in adj.get(u,[]):
   if v not in seen:yield from walk(v,seen|{v},path+[eid],cost+c)
 return list(walk(source,{source},[],0))
def main():
 # Shared branch: both sinks use the same upstream random parent. Independent
 # sink path sampling would falsely produce a 3/4 branch inclusion probability.
 edges=[(0,0,1,1),(1,0,2,1),(2,1,3,1),(3,2,3,1),(4,3,4,1),(5,3,5,1)]
 fixtures=[(edges,0,[4,5]), ([(0,0,1,0),(1,1,0,0),(2,1,2,0),(3,0,2,0)],0,[2]), ([(0,0,1,1),(1,0,1,1),(2,1,2,1)],0,[1,2])]
 tree_checks=0;observed=[]
 for edges,source,sinks in fixtures:
  p=prepare(edges,source,sinks);counts=Counter();n=0
  references={s:simple_paths(edges,source,s) for s in sinks}
  for s,paths in references.items():assert p['distance'][s]==min(x[0] for x in paths)
  keys=list(p['choices'])
  for choices in itertools.product(*(p['choices'][v] for v in keys)):
   tree=materialize(p,dict(zip(keys,choices)));n+=1;tree_checks+=1;counts.update(tree['nodes'])
   for sink,path in tree['paths'].items():assert path in {q for cost,q in references[sink] if cost==p['distance'][sink]}
   assert len(tree['edge_ids'])==len(tree['nodes'])-1
  if source==0 and sinks==[4,5]:assert Fraction(counts[1],n)==Fraction(counts[2],n)==Fraction(1,2)
  for i in range(32):assert sample(p,seed=19,net_id=7,sample_index=i)==sample(p,seed=19,net_id=7,sample_index=i)
  observed.append(dict(trees=n,minimum_costs={str(s):p['distance'][s] for s in sinks}))
 try:prepare([(0,0,1,1)],0,[9])
 except ValueError:pass
 else:raise AssertionError('unreachable accepted')
 O=R/'experiments/shortest_NET_tree_ensemble_core_v1_2026-10-19';O.mkdir();files=[pathlib.Path(__file__).resolve(),R/'tools/shortest_NET_tree_ensemble_v1.py']
 with (O/'verification.json').open('x') as f:json.dump(dict(status='small_graph_shared_parent_ensemble_reference_pass',bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},fixtures=observed,exhaustive_tree_checks=tree_checks,shared_branch_probability='1/2 not independent-sink 3/4',zero_cost_cycles_excluded_by_minimum_hops=True,parallel_edges_preserved=True,real_RR_integration_pending=True,scope='Reference core only. Uniform local parent choices do not imply uniform trees. Min-hop tie restriction excludes longer equal-RC paths; no budget/STA, congestion-quality, timing or family-generalization claim.'),f,indent=2)
 print('PASS',tree_checks,'exhaustive tiny trees; real RR integration pending')
if __name__=='__main__':main()
