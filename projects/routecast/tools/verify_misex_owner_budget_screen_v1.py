"""Independent shortest-distance certificate and exact owner-screen audit."""
import sys,json
from pathlib import Path
from collections import Counter,defaultdict,deque
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
out=R/'experiments/misex_owner_budget_screen_v2_2026-10-07';base=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json');reference=Path(next(k for k in p['inputs'] if k.endswith('misex_owner_limit_alternatives_v1_2026-10-07/receipt.json')));old=json.loads(reference.read_text());bindings={**p['inputs'],**p['sources'],**closure([Path(__file__)]),str(out/'receipt.json'):sha(out/'receipt.json')}
for file in out.glob('screen_NET*.json'):bindings[str(file)]=sha(file)
assert all(sha(k)==v for k,v in bindings.items());(out/'verification_protocol.json').write_text(json.dumps(dict(bindings=bindings))+'\n');graph,digest,nodes,f,rc,_=load_endpoints(base/'endpoints.json');event=json.loads(Path(next(k for k in p['inputs'] if k.endswith('batch7.json'))).read_text());release=set(event['repair_attempts'][0]['released_net_ids']);slots={e:s for s,e in enumerate(f['edge_ids'])};owners=defaultdict(set)
for rec in event['before_records']:
 if rec['net_id'] not in release:owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
rows=[]
for row in r['rows']:
 q=row['query'];budget=row['budget_integer'];banned=set(row['forbidden_nodes']);data=json.loads((out/f"screen_NET{q['net_id']}.json").read_text());forward={int(k):v for k,v in data['forward'].items()};reverse={int(k):v for k,v in data['reverse'].items()};allowed=lambda u:u not in banned and f['capacities'][u]>0
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
  visited={root};queue=deque([root])
  while queue:
   for v in tight[queue.popleft()]:
    if v not in visited:visited.add(v);queue.append(v)
  assert visited==set(dist)
 envelope={u for u,d in forward.items() if u in reverse and d+reverse[u]<=budget};other=Counter(u for net,own in owners.items() if net!=q['net_id'] for u in own);saturated={u for u in envelope if other[u]>=f['capacities'][u]};candidates={net for net,own in owners.items() if net!=q['net_id'] and own.intersection(saturated)};assert envelope==set(data['envelope_nodes']) and saturated==set(data['saturated_nodes']) and candidates==set(data['candidates']);previous=next(x for x in old['rows'] if x['query']==q);previous_by={x['extra_net']:x for x in previous['candidates']};assert previous_by[None]['minimum_within_budget_integer'] is None;assert {x['extra_net'] for x in row['candidates']}=={None}|candidates;assert all(previous_by[x['extra_net']]['minimum_within_budget_integer']==x['minimum_within_budget_integer'] for x in row['candidates']);assert all(x['minimum_within_budget_integer'] is None for x in previous['candidates'] if x['extra_net'] is not None and x['extra_net'] not in candidates)
 for c in row['candidates']:
  if c['minimum_within_budget_integer'] is None:continue
  path=c['physical_edge_ids'];assert rc.path(q['source'],q['sink'],path)==c['minimum_within_budget_integer']<=budget;used={q['source']}|{f['dest_ranks'][slots[e]] for e in path};blocked=other.copy();blocked.subtract(owners[c['extra_net']]);assert not used.intersection(banned) and all(f['capacities'][u]>blocked[u] for u in used)
 rows.append(dict(query_net=q['net_id'],forward_and_reverse_exact_cutoff_certified=True,envelope_owner_candidates_exact=True,reference_conditions=len(previous['candidates']),retained_conditions=len(row['candidates']),all_reference_successes_retained=True,selected_path_rc_budget_capacity_pass=True));print('PASS screen',q['net_id'],len(candidates),flush=True)
assert all(sha(k)==v for k,v in bindings.items());(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Shortest budget-domain certificate via all-arc inequalities/closure and root tight-edge reachability, necessary owner filter after baseline fails; no joint/native proof.'),indent=2)+'\n')
