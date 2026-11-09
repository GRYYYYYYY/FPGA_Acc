"""Independent raw reverse minimum and restoring upper witnesses for next sink."""
import sys,json,heapq
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
out=R/'experiments/misex_continuation_failure_domain_v4_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());bindings={**r['bindings'],**closure([Path(__file__)]),str(rp):sha(rp)};assert all(sha(k)==v for k,v in bindings.items());_,_,nodes,f,rc,_=load_endpoints(R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json');seed=R/'experiments/misex_verified_seed_continuation_v4_2026-10-07/candidate.json';assert str(seed) in bindings;state=json.loads(seed.read_text());owners=defaultdict(set);slots={e:s for s,e in enumerate(f['edge_ids'])}
for rec in state['records']:owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
q=r['query'];src,sink=q['source'],q['sink'];counts=Counter(n for net,ns in owners.items() if net!=q['net_id'] for n in ns);allowed=[f['capacities'][i]>counts[i] for i in range(len(nodes))];rev=[[] for _ in nodes]
for u in range(len(nodes)):
 for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):rev[f['dest_ranks'][s]].append((u,s))
d={};heap=[]
if allowed[sink]:d[sink]=0;heap=[(0,sink)]
while heap:
 value,v=heapq.heappop(heap)
 if d[v]!=value:continue
 for u,s in rev[v]:
  if not allowed[u]:continue
  nd=value+rc.increments[s]
  if nd<d.get(u,float('inf')):d[u]=nd;heapq.heappush(heap,(nd,u))
minimum=None if not allowed[src] or src not in d else rc.initial(src)+d[src];assert (minimum is None)==(r['baseline'] is None)
if minimum is not None:assert minimum==r['baseline']['minimum_integer'] and rc.path(src,sink,r['baseline']['physical_edge_ids'])==minimum and minimum>r['budget']
arcs=0
for u in range(len(nodes)):
 if not allowed[u]:continue
 for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):
  v=f['dest_ranks'][s]
  if allowed[v] and v in d:assert u in d and d[u]<=rc.increments[s]+d[v];arcs+=1
verified=0
for check in r['checks']:
 w=check['witness']
 if w is None:continue
 net=check['extra_net'];used={src}|{f['dest_ranks'][slots[e]] for e in w['physical_edge_ids']};assert rc.path(src,sink,w['physical_edge_ids'])==w['minimum_integer']<=r['budget'];assert all(f['capacities'][n]>counts[n]-int(n in owners[net]) for n in used);verified+=1
assert all(sha(k)==v for k,v in bindings.items());(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,minimum_integer=minimum,all_allowed_arc_checks=arcs,restoring_positive_witnesses_verified=verified,scope='Independent exact baseline plus positive path witnesses; negative domain checks/completeness not certified.'),indent=2)+'\n');print('PASS exact baseline',minimum,'positive witnesses',verified)
