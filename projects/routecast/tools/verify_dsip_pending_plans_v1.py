"""Independent witness union/selection and all saved joint partial states."""
import sys,json,heapq
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from immutable_xml_prediction_audit import ImmutableXMLAudit
base=R/'experiments/mcnc_prospective_v1_2026-10-07/dsip';graph,digest,nodes,f,rc,queries=load_endpoints(base/'endpoints.json');ep=json.loads((base/'endpoints.json').read_text());audit=ImmutableXMLAudit(graph,digest);slots={e:s for s,e in enumerate(f['edge_ids'])};reverse=[[] for _ in nodes]
for u in range(len(nodes)):
 for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):reverse[f['dest_ranks'][s]].append((u,s))
for name in ('dsip_pending_joint_v1_2026-10-07','dsip_pending_prefix_joint_v2_2026-10-07'):
 out=R/'experiments'/name;p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json');bindings={**p['inputs'],**p['sources'],**r['files'],**closure([Path(__file__)]),str(out/'receipt.json'):sha(out/'receipt.json')};assert all(sha(k)==v for k,v in bindings.items());(out/'verification_protocol.json').write_text(json.dumps(dict(bindings=bindings))+'\n');before=json.loads(Path(next(k for k in p['inputs'] if k.endswith('/dsip/candidate.json'))).read_text());owners=defaultdict(set)
 for rec in before['records']:owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
 evidence=json.loads((out/'release_evidence.json').read_text());assert {x['query']['connection_id'] for x in evidence}==set(before['pending_connection_ids']);selected={q['connection_id'] for q in json.loads((out/'requested_queries.json').read_text())};union=set()
 for item in evidence:
  q=item['query'];path=item['physical_edge_ids'];value=rc.path(q['source'],q['sink'],path);assert value==item['minimum_integer'];d={q['sink']:0};heap=[(0,q['sink'])];minimum=None
  while heap:
   dist,u=heapq.heappop(heap)
   if dist!=d[u]:continue
   if u==q['source']:minimum=dist+rc.initial(u);break
   for v,s in reverse[u]:
    if f['capacities'][v]<=0:continue
    nd=dist+rc.increments[s]
    if v not in d or nd<d[v]:d[v]=nd;heapq.heappush(heap,(nd,v))
  assert minimum==value;other=Counter(n for net,own in owners.items() if net!=q['net_id'] for n in own);used={q['source']}|{f['dest_ranks'][slots[e]] for e in path};blocked=sorted(n for n in used if other[n]>=f['capacities'][n]);blocking=sorted(net for net,own in owners.items() if net!=q['net_id'] and own.intersection(blocked));assert blocked==item['blocked_nodes'] and blocking==item['blocking_net_ids']
  if q['connection_id'] in selected:union.update(blocking)
 assert union==set(r['released_net_ids'])
 if 'prefix' in name:
  prefix=[];expected_union=set()
  for item in evidence:
   proposed=expected_union|set(item['blocking_net_ids'])
   if len(proposed)>4:break
   prefix.append(item['query']['connection_id']);expected_union=proposed
  assert prefix==r['pending_ids'] and len(union)<=4
 else:assert r['status']=='OWNER_LIMIT' and len(union)>4
 kept={x['connection_id']:x for x in before['records'] if x['net_id'] not in union};states=0
 for file in sorted(out.glob('branch*/net*.json'))+sorted(out.glob('branch*/joint_candidate.json')):
  c=json.loads(file.read_text());records={x['connection_id']:x for x in c['records']};assert all(records[k]==v for k,v in kept.items());parents=defaultdict(dict)
  for rec in c['records']:
   assert rc.path(rec['source'],rec['sink'],rec['answer']['physical_edge_ids'])==rec['answer']['delay']<=rec['budget_integer'];u=rec['source']
   for e in rec['answer']['physical_edge_ids']:
    arc=audit.graph.edges[e];assert arc.source==u;incoming=(u,e);u=arc.sink;assert u not in parents[rec['net_id']] or parents[rec['net_id']][u]==incoming;parents[rec['net_id']][u]=incoming
  connections=[dict(q,method='searched' if q['connection_id'] in records else 'failed',physical_edge_ids=records[q['connection_id']]['answer']['physical_edge_ids'] if q['connection_id'] in records else None) for q in queries];adapted=dict(connections=connections,physical_graph_sha256=digest,node_occupancy={str(k):v for k,v in c['ledger'].items()},methods=dict(Counter(q['method'] for q in connections)),completed=len(records),requested=len(queries));proof=audit.verify(ep,adapted);assert proof['all_physical_and_union_checks_passed'] and proof['all_type_overuse_units']==0;states+=1
 if r['completed'] is not None:assert r['completed']==len(before['records'])+len(selected)
 assert all(sha(k)==v for k,v in bindings.items());(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,independent_reverse_witnesses=len(evidence),release_selection_exact=True,partial_states_xml_rc_parents_capacity_pass=states,unaffected_identity_pass=True,scope='Local post-limit attempt, not original 8-batch outcome or native proof.'),indent=2)+'\n');print('PASS plan',name,states,flush=True)
