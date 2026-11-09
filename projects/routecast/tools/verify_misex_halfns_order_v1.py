"""Independent original XML/RC/parents/occupancy audit of both partial orders."""
import sys,json
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from immutable_xml_prediction_audit import ImmutableXMLAudit
out=R/'experiments/misex_halfns_order_v1_2026-10-07';base=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3';p=json.loads((out/'protocol.json').read_text());receipt=json.loads((out/'receipt.json').read_text());assert receipt['protocol_sha256']==sha(out/'protocol.json');bindings={**p['inputs'],**p['sources'],**closure([Path(__file__)]),str(out/'receipt.json'):sha(out/'receipt.json')}
for row in receipt['rows']:bindings.update(row['files'])
assert all(sha(k)==v for k,v in bindings.items());(out/'verification_protocol.json').write_text(json.dumps(dict(bindings=bindings))+'\n');graph,digest,nodes,f,rc,queries=load_endpoints(base/'endpoints.json');a=ImmutableXMLAudit(graph,digest);ep=json.loads((base/'endpoints.json').read_text());rows=[]
for row in receipt['rows']:
 c=json.loads((out/row['policy']/'candidate.json').read_text());records={r['connection_id']:r for r in c['records']};parents=defaultdict(dict)
 for r in c['records']:
  assert rc.path(r['source'],r['sink'],r['answer']['physical_edge_ids'])==r['answer']['delay']<=r['budget_integer'];u=r['source']
  for e in r['answer']['physical_edge_ids']:
   edge=a.graph.edges[e];assert edge.source==u;incoming=(u,e);u=edge.sink;assert u not in parents[r['net_id']] or parents[r['net_id']][u]==incoming;parents[r['net_id']][u]=incoming
 connections=[dict(q,method='searched' if q['connection_id'] in records else 'failed',physical_edge_ids=records[q['connection_id']]['answer']['physical_edge_ids'] if q['connection_id'] in records else None) for q in queries];adapted=dict(connections=connections,physical_graph_sha256=digest,node_occupancy={str(k):v for k,v in c['ledger'].items()},methods=dict(Counter(q['method'] for q in connections)),completed=len(records),requested=len(queries));audit=a.verify(ep,adapted);assert audit['all_physical_and_union_checks_passed'] and audit['all_type_overuse_units']==0;rows.append(dict(policy=row['policy'],completed=len(records),original_xml_audit=audit,exact_rc_parents_pass=True,scope='Partial diagnostic state only, not committed or native proof.'));print('PASS',row['policy'],flush=True)
assert all(sha(k)==v for k,v in bindings.items());(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows),indent=2)+'\n')
