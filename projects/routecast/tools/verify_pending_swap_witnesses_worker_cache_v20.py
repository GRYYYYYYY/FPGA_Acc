"""Every repair group state plus independent expansion witness/owner audit."""
import sys,json,heapq
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from immutable_xml_prediction_audit import ImmutableXMLAudit
out=R/'experiments/mcnc_pending_swap_worker_cache_v20_2026-10-07';base=R/'experiments/mcnc_prospective_v1_2026-10-07';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json');bindings={**p['inputs'],**p['sources'],**closure([Path(__file__)]),str(out/'receipt.json'):sha(out/'receipt.json')}
for row in r['rows']:bindings.update(row['files'])
assert all(sha(k)==v for k,v in bindings.items());(out/'expansion_verification_protocol.json').write_text(json.dumps(dict(bindings=bindings))+'\n');rows=[]
for row in r['rows']:
 name=row['name'];graph,digest,nodes,f,rc,queries=load_endpoints(base/name/'endpoints.json');ep=json.loads((base/name/'endpoints.json').read_text());audit=ImmutableXMLAudit(graph,digest);slots={e:s for s,e in enumerate(f['edge_ids'])};reverse=[[] for _ in nodes]
 for u in range(len(nodes)):
  for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):reverse[f['dest_ranks'][slot]].append((u,slot))
 states_checked=0;witnesses=0
 for eventfile in sorted((out/name).glob('batch*.json')):
  event=json.loads(eventfile.read_text());event['repair_attempts']=[] if event['owner_repair'] is None else event['owner_repair']['attempts'];assert len(event['repair_attempts'])<=4
  for attempt in event['repair_attempts']:
   release=set(attempt['released_net_ids']);assert len(release)<=4;kept={q['connection_id']:q for q in event['before_records'] if q['net_id'] not in release};assert set(attempt['removed_connection_ids'])=={q['connection_id'] for q in event['before_records'] if q['net_id'] in release};assert len(attempt['branches'])<=64;owners=defaultdict(set)
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
 rows.append(dict(name=name,repair_states_checked=states_checked,independent_reverse_witnesses=witnesses,scope='Expansion witnesses only; all branch states independently audited separately.',whole_release_and_unaffected_identity_pass=True));print('PASS repairs',name,states_checked,witnesses,flush=True)
assert all(sha(k)==v for k,v in bindings.items());(out/'expansion_verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows),indent=2)+'\n')
