"""Independent weighted Dijkstra and complete parent/path audit, sequential calls."""
from pathlib import Path
from types import SimpleNamespace
from collections import Counter
import random,heapq,json
from pre_route_endpoints import sha
from compatible_multi_bidi_search_v1 import Search
R=Path(__file__).resolve().parents[1];O=R/'experiments/compatible_multi_bidi_contract_v1_2026-10-10';O.mkdir(exist_ok=True);binary=R/'experiments/soft_demand_workspace_radix_build_v3_2026-10-08/search.so';counts=Counter();witness=None
for seed in range(300):
 rng=random.Random(seed);n=rng.randrange(5,36);f=dict(row_offsets=[0],dest_ranks=[],capacities=[1]*n,edge_ids=[]);inc=[]
 for u in range(n):
  for v in range(n):
   if rng.random()<.15 or v==(u+1)%n:f['dest_ranks'].append(v);inc.append(rng.choice([0,0,1,5,2**40]));f['edge_ids'].append(len(inc)-1)
  f['row_offsets'].append(len(inc))
 rc=SimpleNamespace(increments=inc,initial=lambda u:u%7);s=Search(f,rc,binary)
 for step in range(12):
  src=rng.randrange(n);targets=set(rng.sample(range(n),rng.randrange(2,5)));prices={u:rng.randrange(8) for u in range(n)};weight=[0,1,17,2**63][step%4];s.prepare(prices,weight)
  d={src:src%7};q=[(d[src],src)]
  while q:
   cost,u=heapq.heappop(q)
   if cost!=d[u]:continue
   for e in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    v=f['dest_ranks'][e]
    if not f['capacities'][v]:continue
    new=cost+inc[e]+weight*prices[v]
    if new<d.get(v,2**200):d[v]=new;heapq.heappush(q,(new,v))
  before=s.stats['parent_conflict_fallback'];raw,parent,found=s.search(src,targets);assert found==targets&d.keys()
  for t in sorted(found):
   u=t;seen={u};path=[]
   while u!=src:
    prev,e=parent[u];assert f['row_offsets'][prev]<=e<f['row_offsets'][prev+1] and f['dest_ranks'][e]==u;assert prev not in seen;seen.add(prev);path.append(e);u=prev
   delay=src%7+sum(inc[e] for e in path);objective=delay+sum(weight*prices[f['dest_ranks'][e]] for e in path);assert raw[t]==delay and objective==d[t];counts['paths']+=1
  if s.stats['parent_conflict_fallback']>before and witness is None:witness=dict(seed=seed,step=step,source=src,targets=sorted(targets),prices=prices,weight=weight,fields=f,increments=inc)
  # Restore through a rejected preparation and exercise the next real search.
  try:s.prepare({0:-1},weight)
  except ValueError:pass
  else:raise AssertionError('negative price accepted')
  counts['queries']+=1
 counts.update(s.stats);s.close()
 try:s.search(0,{1,2})
 except RuntimeError:counts['closed_rejections']+=1
 else:raise AssertionError('closed result accepted')
fixtures=[]
for name,n,edges,caps,targets,expected,branch in [
 ('unreachable',5,[(0,1,2),(1,2,2)],[1]*5,{2,4},{2},'unreachable_fallback'),
 ('zero_capacity',5,[(0,1,1),(1,2,1)],[1,1,0,1,1],{1,2},{1},'capacity_fallback'),
 ('above_target_limit',6,[(i,i+1,1) for i in range(5)],[1]*6,set(range(1,6)),set(range(1,6)),'original_policy'),
 ('empty_targets',3,[(0,1,0)],[1]*3,set(),set(),'original_policy'),
 ('source_is_target',3,[(0,1,0),(1,0,0)],[1]*3,{0,1},{0,1},'merged')]:
 f=dict(row_offsets=[0],dest_ranks=[],capacities=caps,edge_ids=[]);inc=[]
 for u in range(n):
  for a,b,c in edges:
   if a==u:f['dest_ranks'].append(b);inc.append(c);f['edge_ids'].append(len(inc)-1)
  f['row_offsets'].append(len(inc))
 rc=SimpleNamespace(increments=inc,initial=lambda u:0);candidate=Search(f,rc,binary);candidate.prepare({},1);raw,parent,found=candidate.search(0,targets);assert found==expected and candidate.stats[branch]==1
 # Caller mutations cannot alter private graph/electrical snapshots.
 if inc:inc[0]=9999;f['dest_ranks'][0]=n+100
 again=candidate.search(0,targets);assert again[2]==expected
 for t in found:assert again[0][t]==raw[t]
 try:candidate.prepare({0:2**64-1},2**64-1)
 except ValueError:pass
 else:raise AssertionError('overflow envelope admitted')
 assert candidate.search(0,targets)[2]==expected
 fixtures.append(dict(case=name,branch=branch,found=sorted(found),private_input_and_failed_prepare_preservation=True));candidate.close()
assert counts['queries']==3600 and counts['merged']>0 and counts['parent_conflict_fallback']>0
if witness:(O/'parent_conflict_witness.json').write_text(json.dumps(witness,indent=2)+'\n')
files=[Path(__file__).resolve(),R/'tools/compatible_multi_bidi_search_v1.py',R/'tools/hybrid_bidirectional_search_v1.py',R/'tools/soft_demand_workspace_bridge_v1.py',R/'tools/soft_demand_cpp_bridge_v1.py',R/'tools/bidirectional_rc_bridge_v1.py',binary,R/'experiments/bidirectional_rc_build_v2_2026-10-08/search.so']
(O/'verification.json').write_text(json.dumps(dict(bindings={str(p):sha(p) for p in files},random_graphs=300,counts=dict(counts),fixtures=fixtures,all_requested_minimum_objectives_raw_delays_directed_paths_singleparent_pass=True,scope='New small-target tie/path policy, standalone128 only. Random zero-cost ties, wide weights, source among targets, real merge/forward conflict fallbacks and sequential recovery. No path identity or complete realmodel/native/performance claim.'),indent=2)+'\n');print(dict(counts))
