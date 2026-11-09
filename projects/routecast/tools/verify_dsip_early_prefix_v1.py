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
for name in ('dsip_early_prefix_v1_2026-10-07',):
 out=R/'experiments'/name;p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json');bindings={**p['inputs'],**p['sources'],**r['files'],**closure([Path(__file__)]),str(out/'receipt.json'):sha(out/'receipt.json')};assert all(sha(k)==v for k,v in bindings.items());(out/'verification_protocol.json').write_text(json.dumps(dict(bindings=bindings))+'\n');event=json.loads(Path(next(k for k in p['inputs'] if k.endswith('/dsip/batch8.json'))).read_text());before=dict(records=event['before_records']);before['pending_connection_ids']=[q['connection_id'] for q in queries if q['connection_id'] not in {x['connection_id'] for x in before['records']}];owners=defaultdict(set)
 for rec in before['records']:owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
 selection=json.loads((out/'selection.json').read_text());evidence=selection['witness_evidence'];selected=set(selection['requested_connection_ids']);union=set();expected=[]
 ordered=sorted([q for q in queries if q['connection_id'] in before['pending_connection_ids']],key=lambda q:(q['net_id'],q['connection_id']))
 assert [x['query'] for x in evidence]==ordered[:len(evidence)] and len(evidence)<=16
 for item in evidence:
  q=item['query'];path=item['witness']['physical_edge_ids'];value=rc.path(q['source'],q['sink'],path);assert value==item['witness']['minimum_integer'];d={q['sink']:0};heap=[(0,q['sink'])];minimum=None
  while heap:
   dist,u=heapq.heappop(heap)
   if dist!=d[u]:continue
   if u==q['source']:minimum=dist+rc.initial(u);break
   for v,s in reverse[u]:
    if f['capacities'][v]<=0:continue
    nd=dist+rc.increments[s]
    if v not in d or nd<d[v]:d[v]=nd;heapq.heappush(heap,(nd,v))
  assert minimum==value;other=Counter(n for net,own in owners.items() if net!=q['net_id'] for n in own);used={q['source']}|{f['dest_ranks'][slots[e]] for e in path};blocked=sorted(n for n in used if other[n]>=f['capacities'][n]);blocking=sorted(net for net,own in owners.items() if net!=q['net_id'] and own.intersection(blocked));assert blocked==item['blocked_nodes'] and blocking==item['blocking_net_ids'];proposed=union|set(blocking);assert sorted(proposed)==item['cumulative_release'] and item['selected']==(len(proposed)<=4)
  if item['selected']:union=proposed;expected.append(q['connection_id'])
  else:assert item is evidence[-1] and selection['stop']=='OWNER_LIMIT'
 assert expected==selection['requested_connection_ids']==r['requested_ids'] and union==set(r['released_net_ids']) and len(union)<=4
 assert selection['remaining_pending_ids']==[q['connection_id'] for q in ordered if q['connection_id'] not in selected]
 assert selection['removed_connection_ids']==r['removed_ids']==[x['connection_id'] for x in before['records'] if x['net_id'] in union]
 kept={x['connection_id']:x for x in before['records'] if x['net_id'] not in union};states=0
 for file in sorted(out.glob('branch*/net*.json'))+sorted(out.glob('branch*/joint_candidate.json')):
  c=json.loads(file.read_text());records={x['connection_id']:x for x in c['records']};assert all(records[k]==v for k,v in kept.items());parents=defaultdict(dict)
  for rec in c['records']:
   assert rc.path(rec['source'],rec['sink'],rec['answer']['physical_edge_ids'])==rec['answer']['delay']<=rec['budget_integer'];u=rec['source']
   for e in rec['answer']['physical_edge_ids']:
    arc=audit.graph.edges[e];assert arc.source==u;incoming=(u,e);u=arc.sink;assert u not in parents[rec['net_id']] or parents[rec['net_id']][u]==incoming;parents[rec['net_id']][u]=incoming
   if file.name.startswith('net'):
    branch=json.loads((file.parent/'branch.json').read_text());forbidden={n for net,n in branch['constraints'] if net==rec['net_id']};used={rec['source']}|{f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids']};assert not used.intersection(forbidden)
  connections=[dict(q,method='searched' if q['connection_id'] in records else 'failed',physical_edge_ids=records[q['connection_id']]['answer']['physical_edge_ids'] if q['connection_id'] in records else None) for q in queries];adapted=dict(connections=connections,physical_graph_sha256=digest,node_occupancy={str(k):v for k,v in c['ledger'].items()},methods=dict(Counter(q['method'] for q in connections)),completed=len(records),requested=len(queries));proof=audit.verify(ep,adapted);assert proof['all_physical_and_union_checks_passed'] and proof['all_type_overuse_units']==0;states+=1
 if r['completed'] is not None:
  final=json.loads((out/'joint_result.json').read_text())['solution'];assert r['completed']==len(before['records'])+len(selected)==final['completed_connections'];assert {x['connection_id'] for x in final['records']}=={x['connection_id'] for x in before['records']}|selected;assert r['global_required']==len(queries)
 assert all(sha(k)==v for k,v in bindings.items());(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,independent_reverse_witnesses=len(evidence),release_selection_exact=True,partial_states_xml_rc_parents_capacity_pass=states,unaffected_identity_pass=True,scope='Early snapshot component, not fresh full sequence or native proof.'),indent=2)+'\n');print('PASS plan',name,states,flush=True)
