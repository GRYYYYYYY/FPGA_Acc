"""Independent budget-domain and every checked extra-owner condition proof."""
import sys,json,heapq
from pathlib import Path
from collections import Counter,defaultdict,deque
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
out=R/'experiments/bigkey_pending_owner_repair_v1_2026-10-07';base=R/'experiments/mcnc_prospective_v1_2026-10-07';r=json.loads((out/'receipt.json').read_text());bindings={**r['bindings'],**r['files'],**closure([Path(__file__)]),str(out/'receipt.json'):sha(out/'receipt.json')};result=json.loads((out/'result.json').read_text());original_event=Path(next(k for k in r['bindings'] if k.endswith('/bigkey/batch2.json')));r['rows']=[dict(name='bigkey',files=r['files'])]
assert all(sha(k)==v for k,v in bindings.items());(out/'fallback_verification_protocol.json').write_text(json.dumps(dict(bindings=bindings))+'\n');rows=[]
for row in r['rows']:
 graph,digest,nodes,f,rc,queries=load_endpoints(base/row['name']/'endpoints.json');slots={e:s for s,e in enumerate(f['edge_ids'])};reverse_arcs=[[] for _ in nodes]
 for u in range(len(nodes)):
  for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):reverse_arcs[f['dest_ranks'][s]].append((u,s))
 domains=0;checks=0
 for eventfile in [original_event]:
  event=json.loads(eventfile.read_text());event['repair_attempts']=result['attempts'];batch_domains=0;batch_checks=0
  for attempt in event['repair_attempts']:
   released=set(attempt['released_net_ids']);owners=defaultdict(set)
   for rec in event['before_records']:
    if rec['net_id'] not in released:owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
   for fallback in attempt['fallback_evidence']:
    batch_domains+=1;domains+=1;q=fallback['query'];budget=fallback['budget_integer'];banned=set(fallback['forbidden_nodes']);data=fallback['domain'];forward={int(k):v for k,v in data['forward'].items()};reverse={int(k):v for k,v in data['reverse'].items()};allowed=lambda u:u not in banned and f['capacities'][u]>0
    for dist,root,start,limit,backward in ((forward,q['source'],rc.initial(q['source']),budget,False),(reverse,q['sink'],0,budget-rc.initial(q['source']),True)):
     assert dist[root]==start and all(allowed(u) and start<=d<=limit for u,d in dist.items());tight=defaultdict(list)
     for u in range(len(nodes)):
      if not allowed(u):continue
      for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
       v=f['dest_ranks'][slot]
       if not allowed(v):continue
       a,b=(v,u) if backward else (u,v)
       if a in dist and dist[a]+rc.increments[slot]<=limit:
        assert b in dist and dist[b]<=dist[a]+rc.increments[slot]
        if dist[b]==dist[a]+rc.increments[slot]:tight[a].append(b)
     seen={root};queue=deque([root])
     while queue:
      for v in tight[queue.popleft()]:
       if v not in seen:seen.add(v);queue.append(v)
     assert seen==set(dist)
    envelope={u for u,d in forward.items() if u in reverse and d+reverse[u]<=budget};other=Counter(u for net,own in owners.items() if net!=q['net_id'] for u in own);saturated={u for u in envelope if other[u]>=f['capacities'][u]};candidates={net for net,own in owners.items() if net!=q['net_id'] and own.intersection(saturated)};assert envelope==set(data['envelope_nodes']) and saturated==set(data['saturated_nodes']) and candidates==set(data['candidates'])
    for extra,witness in [(None,fallback['baseline'])]+[(c['extra_net'],c['witness']) for c in fallback['checks']]:
     if extra is not None:assert extra in candidates;checks+=1;batch_checks+=1
     occupancy=other.copy()
     if extra is not None:occupancy.subtract(owners[extra])
     capacity_allowed=lambda u:allowed(u) and f['capacities'][u]>occupancy[u];dist={q['sink']:0} if capacity_allowed(q['source']) and capacity_allowed(q['sink']) else {};heap=[(d,u) for u,d in dist.items()];minimum=None
     while heap:
      d,u=heapq.heappop(heap)
      if dist[u]!=d:continue
      if d+rc.initial(q['source'])>budget:break
      if u==q['source']:minimum=d+rc.initial(u);break
      for v,s in reverse_arcs[u]:
       if not capacity_allowed(v):continue
       nd=d+rc.increments[s]
       if v not in dist or nd<dist[v]:dist[v]=nd;heapq.heappush(heap,(nd,v))
     assert minimum==(None if witness is None else witness['minimum_integer'])
     if witness is not None:
      assert rc.path(q['source'],q['sink'],witness['physical_edge_ids'])==minimum<=budget;used={q['source']}|{f['dest_ranks'][slots[e]] for e in witness['physical_edge_ids']};assert all(capacity_allowed(u) for u in used)
    if fallback['baseline'] is not None:assert fallback['status']=='BASELINE_ALREADY_FEASIBLE_NOT_FILTERED' and not fallback['checks']
    else:assert fallback['status']=='BASELINE_FAILED_FILTER_VALID'
    for check in fallback['checks']:assert check['expanded_release']==sorted(released|{check['extra_net']}) and len(check['expanded_release'])<=4
  assert batch_domains<=4 and batch_checks<=32
 rows.append(dict(name=row['name'],domains=domains,owner_checks=checks,all_distance_owner_baseline_and_path_certificates_pass=True,bounds_pass=True));print('PASS fallback',row['name'],domains,checks,flush=True)
assert all(sha(k)==v for k,v in bindings.items());(out/'fallback_verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows),indent=2)+'\n')
