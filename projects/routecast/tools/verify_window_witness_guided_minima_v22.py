"""Independent full raw reverse Dijkstra for every recorded candidate query."""
import sys,json,heapq
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
out=R/'experiments/misex_net_window_witness_guided_v22_2026-10-07';receipt=out/'receipt.json';r=json.loads(receipt.read_text());bindings={**r['bindings'],**closure([Path(__file__)]),str(receipt):sha(receipt)};assert all(sha(k)==v for k,v in bindings.items())
parent=R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07';event=json.loads(Path(r['event_file']).read_text());floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads((parent/'misex3/floors.json').read_text())};_,_,nodes,f,rc,_=load_endpoints(R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json');slots={e:s for s,e in enumerate(f['edge_ids'])};owners=defaultdict(set)
for rec in event['before_records']:owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
reverse=[[] for _ in nodes]
for u in range(len(nodes)):
 for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):reverse[f['dest_ranks'][s]].append((u,s))
p=r;count=0;arcs=0
for root in p['checks']:
 assert [row['query'] for row in root['queries']]==event['selection']['queries']
 for row in root['queries']:
  q=row['query'];src,sink=q['source'],q['sink'];occupancy=Counter(node for net,ns in owners.items() if net not in root['release'] and net!=q['net_id'] for node in ns);allowed=[f['capacities'][i]>occupancy[i] for i in range(len(nodes))];dist={};queue=[]
  if allowed[sink]:dist[sink]=0;queue=[(0,sink)]
  while queue:
   d,v=heapq.heappop(queue)
   if dist[v]!=d:continue
   for u,s in reverse[v]:
    if not allowed[u]:continue
    nd=d+rc.increments[s]
    if nd<dist.get(u,float('inf')):dist[u]=nd;heapq.heappush(queue,(nd,u))
  for u in range(len(nodes)):
   if not allowed[u]:continue
   for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    v=f['dest_ranks'][s]
    if allowed[v] and v in dist:assert u in dist and dist[u]<=rc.increments[s]+dist[v];arcs+=1
  minimum=None if not allowed[src] or src not in dist else rc.initial(src)+dist[src];w=row['witness'];assert (w is None)==(minimum is None)
  if w is not None:
   assert w['minimum_integer']==minimum and rc.path(src,sink,w['physical_edge_ids'])==minimum;assert allowed[src] and all(allowed[f['dest_ranks'][slots[e]]] for e in w['physical_edge_ids'])
  budget=max(rc.scale//10**9,(3*floors[(src,sink)]+1)//2);assert row['budget']==budget and row['ordinary_budget_feasible']==(minimum is not None and minimum<=budget);count+=1
 assert root['all_selected_ordinary_budget_feasible']==all(x['ordinary_budget_feasible'] for x in root['queries'])
assert p['proposed']==[root['release'] for root in p['checks'] if root['all_selected_ordinary_budget_feasible']];assert all(sha(k)==v for k,v in bindings.items());(out/'minima_verification.json').write_text(json.dumps(dict(queries_verified=count,all_allowed_arc_checks=arcs,bindings=bindings,scope='Every recorded root minimum and witness independently verified; domain completeness and candidate coverage not certified.'),indent=2)+'\n');print('PASS independent minima',count,arcs,flush=True)
