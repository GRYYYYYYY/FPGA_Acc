"""Independent reverse-Dijkstra proof of saved core deletion checks."""
import json,sys,heapq
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
out=R/'experiments/misex_net466_minimal_cores_v1_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());bindings={**r['bindings'],**closure([Path(__file__)]),str(rp):sha(rp)};assert all(sha(k)==v for k,v in bindings.items());parent=R/'experiments/misex_net466_extra_owner_joint_v9_2026-10-07';source=json.loads((parent/'receipt.json').read_text());event=json.loads((parent/'event.json').read_text());_,_,nodes,f,rc,_=load_endpoints(R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json');slots={e:i for i,e in enumerate(f['edge_ids'])};owners=defaultdict(set);reverse=[[] for _ in nodes]
for rec in event['before_records']:owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
for u in range(len(nodes)):
 for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):reverse[f['dest_ranks'][s]].append((u,s))
count=arcs=reductions=0
for row in r['rows']:
 a=source['attempts'][row['attempt']];b=a['branches'][row['branch']];assert a['release']==row['release'];c=next(x for x in b['ordinary_cores'] if x['query']==row['query']);assert row['original_bans']==c['bans'] and row['budget']==c['budget'];q=row['query'];current=set(row['original_bans']);occ=Counter(n for net,own in owners.items() if net not in row['release'] and net!=q['net_id'] for n in own)
 for t in row['tests']:
  trial=current-{t['removed_node']};assert sorted(trial)==t['bans'];allowed=[i not in trial and f['capacities'][i]>occ[i] for i in range(len(nodes))];dist={};queue=[]
  if allowed[q['sink']]:dist[q['sink']]=0;queue=[(0,q['sink'])]
  while queue:
   d,v=heapq.heappop(queue)
   if dist[v]!=d:continue
   for u,s in reverse[v]:
    if not allowed[u]:continue
    nd=d+rc.increments[s]
    if nd<dist.get(u,float('inf')):dist[u]=nd;heapq.heappush(queue,(nd,u))
  minimum=None if not allowed[q['source']] or q['source'] not in dist else rc.initial(q['source'])+dist[q['source']];assert minimum==t['minimum_integer'];infeasible=minimum is None or minimum>row['budget'];assert infeasible==t['ordinary_infeasible']
  for u in range(len(nodes)):
   if not allowed[u]:continue
   for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    v=f['dest_ranks'][s]
    if allowed[v] and v in dist:assert u in dist and dist[u]<=rc.increments[s]+dist[v];arcs+=1
  if minimum is not None:assert rc.path(q['source'],q['sink'],t['physical_edge_ids'])==minimum
  if infeasible:current=trial;reductions+=1
  count+=1
 assert sorted(current)==row['reduced_bans']
assert count==r['checks'];assert all(sha(k)==v for k,v in bindings.items());(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,tests_verified=count,arc_checks=arcs,removed_constraints=reductions,scope='Recorded deletions only, not globally minimum cores or routing completeness.'),indent=2)+'\n');print('PASS reduced cores',count,arcs,reductions)
