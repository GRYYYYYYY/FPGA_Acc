"""Every repair group state plus independent expansion witness/owner audit."""
import sys,json,heapq
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from immutable_xml_prediction_audit import ImmutableXMLAudit
out=R/'experiments/mcnc_bounded_owner_joint_v8_2026-10-07';base=R/'experiments/mcnc_prospective_v1_2026-10-07';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json');bindings={**p['inputs'],**p['sources'],**closure([Path(__file__)]),str(out/'receipt.json'):sha(out/'receipt.json')}
for row in r['rows']:bindings.update(row['files'])
assert all(sha(k)==v for k,v in bindings.items());(out/'repair_verification_protocol.json').write_text(json.dumps(dict(bindings=bindings))+'\n');rows=[]
for row in r['rows']:
 name=row['name'];graph,digest,nodes,f,rc,queries=load_endpoints(base/name/'endpoints.json');ep=json.loads((base/name/'endpoints.json').read_text());audit=ImmutableXMLAudit(graph,digest);slots={e:s for s,e in enumerate(f['edge_ids'])};reverse=[[] for _ in nodes]
 for u in range(len(nodes)):
  for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):reverse[f['dest_ranks'][slot]].append((u,slot))
 states_checked=0;witnesses=0
 for eventfile in sorted((out/name).glob('batch*.json')):
  event=json.loads(eventfile.read_text());assert len(event['repair_attempts'])<=4
  for attempt in event['repair_attempts']:
   release=set(attempt['released_net_ids']);assert len(release)<=4;kept={q['connection_id']:q for q in event['before_records'] if q['net_id'] not in release};assert set(attempt['removed_connection_ids'])=={q['connection_id'] for q in event['before_records'] if q['net_id'] in release};assert len(attempt['branches'])<=32;owners=defaultdict(set)
   for rec in kept.values():owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
   for evidence in attempt['expansion_evidence']:
    q=evidence['query'];w=evidence['witness'];banned=set(evidence['forbidden_nodes']);assert rc.path(q['source'],q['sink'],w['physical_edge_ids'])==w['minimum_integer']<=evidence['budget_integer'];used={q['source']}|{f['dest_ranks'][slots[e]] for e in w['physical_edge_ids']};assert not used.intersection(banned);d={q['sink']:0};heap=[(0,q['sink'])];minimum=None
    while heap:
     value,v=heapq.heappop(heap)
     if value!=d[v]:continue
     if v==q['source']:minimum=value+rc.initial(v);break
     for u,slot in reverse[v]:
      if u in banned or f['capacities'][u]<=0:continue
      nd=value+rc.increments[slot]
      if u not in d or nd<d[u]:d[u]=nd;heapq.heappush(heap,(nd,u))
    assert minimum==w['minimum_integer'];other=Counter(n for net,own in owners.items() if net!=q['net_id'] for n in own);blocked=sorted(n for n in used if other[n]>=f['capacities'][n]);blockers=sorted(net for net,own in owners.items() if net!=q['net_id'] and own.intersection(blocked));assert blocked==evidence['blocked_nodes'] and blockers==evidence['blocking_net_ids'] and sorted(release|set(blockers))==evidence['expanded_release'];witnesses+=1
   for branch in attempt['branches']:
    directory=out/name/f"repair_batch{event['index']}_attempt{attempt['index']}_branch{branch['index']}";metadata=json.loads((directory/'branch.json').read_text());assert metadata['branch']==branch and set(metadata['released_net_ids'])==release
    for file in sorted(directory.glob('net*.json')):
     c=json.loads(file.read_text());byid={q['connection_id']:q for q in c['records']};assert all(byid[cid]==record for cid,record in kept.items());parents=defaultdict(dict)
     for rec in c['records']:
      assert rc.path(rec['source'],rec['sink'],rec['answer']['physical_edge_ids'])==rec['answer']['delay']<=rec['budget_integer'];u=rec['source']
      for e in rec['answer']['physical_edge_ids']:
       arc=audit.graph.edges[e];assert arc.source==u;incoming=(u,e);u=arc.sink;assert u not in parents[rec['net_id']] or parents[rec['net_id']][u]==incoming;parents[rec['net_id']][u]=incoming
      forbidden={n for net,n in branch['constraints'] if net==rec['net_id']};used={rec['source']}|{f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids']};assert not forbidden.intersection(used)
     connections=[dict(q,method='searched' if q['connection_id'] in byid else 'failed',physical_edge_ids=byid[q['connection_id']]['answer']['physical_edge_ids'] if q['connection_id'] in byid else None) for q in queries];adapted=dict(connections=connections,physical_graph_sha256=digest,node_occupancy={str(k):v for k,v in c['ledger'].items()},methods=dict(Counter(q['method'] for q in connections)),completed=len(byid),requested=len(queries));a=audit.verify(ep,adapted);assert a['all_physical_and_union_checks_passed'] and a['all_type_overuse_units']==0;states_checked+=1
 rows.append(dict(name=name,repair_states_checked=states_checked,independent_reverse_witnesses=witnesses,all_partial_xml_rc_parents_capacity_and_constraints_pass=True,whole_release_and_unaffected_identity_pass=True));print('PASS repairs',name,states_checked,witnesses,flush=True)
assert all(sha(k)==v for k,v in bindings.items());(out/'repair_verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows),indent=2)+'\n')
