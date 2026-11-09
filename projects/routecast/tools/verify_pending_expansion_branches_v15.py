"""Independent physical audit of all saved branch states, including failures."""
import sys,json
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from immutable_xml_prediction_audit import ImmutableXMLAudit
out=R/'experiments/mcnc_pending_expansion_v15_2026-10-07';p=json.loads((out/'protocol.json').read_text());receipt=json.loads((out/'receipt.json').read_text());bindings={**p['inputs'],**p['sources'],**closure([Path(__file__)]),str(out/'receipt.json'):sha(out/'receipt.json')};assert receipt['protocol_sha256']==sha(out/'protocol.json')
for row in receipt['rows']:bindings.update(row['files'])
assert all(sha(k)==v for k,v in bindings.items());(out/'branch_verification_protocol.json').write_text(json.dumps(dict(bindings=bindings))+'\n');rows=[]
for row in receipt['rows']:
 name=row['name'];base=R/'experiments/mcnc_prospective_v1_2026-10-07'/name;graph,digest,nodes,f,rc,queries=load_endpoints(base/'endpoints.json');ep=json.loads((base/'endpoints.json').read_text());audit=ImmutableXMLAudit(graph,digest);querymap={q['connection_id']:q for q in queries};slots={e:s for s,e in enumerate(f['edge_ids'])};count=0
 for directory in sorted((out/name).glob('repair_batch*_attempt*_branch*')):
  batch=int(directory.name.split('_')[1][5:]);event=json.loads((out/name/f'batch{batch}.json').read_text());meta=json.loads((directory/'branch.json').read_text());trace_attempt=int(directory.name.split('_')[2][7:]);branch_index=int(directory.name.split('_')[3][6:]);attempt= None if trace_attempt==1 else event['owner_repair']['attempts'][trace_attempt-2];expected_release=event['initial_release_net_ids'] if attempt is None else attempt['released_net_ids'];expected_branch=event['repair_attempts'][branch_index] if attempt is None else attempt['branches'][branch_index];assert meta['released_net_ids']==expected_release and meta['branch']==expected_branch;release=set(meta['released_net_ids']);kept={r['connection_id']:r for r in event['before_records'] if r['net_id'] not in release};allowed={r['connection_id'] for r in event['before_records']}|set(event['selection']['requested_connection_ids'])
  for file in sorted(directory.glob('net*.json'))+sorted(directory.glob('joint_candidate.json')):
   state=json.loads(file.read_text());records={r['connection_id']:r for r in state['records']};assert len(records)==len(state['records']) and set(records)<=allowed and all(records[cid]==r for cid,r in kept.items());parents=defaultdict(dict)
   for rec in records.values():
    q=querymap[rec['connection_id']];assert all(q[k]==rec[k] for k in ('net_id','source','sink'));edges=rec['answer']['physical_edge_ids'];assert rc.path(rec['source'],rec['sink'],edges)==rec['answer']['delay']<=rec['budget_integer'];u=rec['source']
    for e in edges:
     arc=audit.graph.edges[e];assert arc.source==u;incoming=(u,e);u=arc.sink;assert u not in parents[rec['net_id']] or parents[rec['net_id']][u]==incoming;parents[rec['net_id']][u]=incoming
    forbidden={node for net,node in meta['branch']['constraints'] if net==rec['net_id']};used={rec['source']}|{f['dest_ranks'][slots[e]] for e in edges};assert not forbidden.intersection(used)
   connections=[dict(q,method='searched' if q['connection_id'] in records else 'failed',physical_edge_ids=records[q['connection_id']]['answer']['physical_edge_ids'] if q['connection_id'] in records else None) for q in queries];adapted=dict(connections=connections,physical_graph_sha256=digest,node_occupancy={str(k):v for k,v in state['ledger'].items()},methods=dict(Counter(q['method'] for q in connections)),completed=len(records),requested=len(queries));proof=audit.verify(ep,adapted);assert proof['all_physical_and_union_checks_passed'] and proof['all_type_overuse_units']==0
   if file.name=='joint_candidate.json':assert set(records)==allowed
   count+=1
 rows.append(dict(name=name,states=count,all_xml_rc_parents_capacity_constraints_and_unaffected_checks_pass=True));print('PASS branches',name,count,flush=True)
assert all(sha(k)==v for k,v in bindings.items());(out/'branch_verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='All archived low-level states and merged candidates, including failed branches; no native proof.'),indent=2)+'\n')
