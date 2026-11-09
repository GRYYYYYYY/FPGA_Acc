"""Independent partial-cohort XML/RC and all released/unaffected records audit."""
import json,sys
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from immutable_xml_prediction_audit import ImmutableXMLAudit
base=R/'experiments/mcnc_prospective_v1_2026-10-07/dsip';out=R/'experiments/dsip_reinsert_order_v2_2026-10-07';r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json');bindings={**p['inputs'],**p['sources'],**closure([Path(__file__)]),str(out/'receipt.json'):sha(out/'receipt.json')};assert all(sha(path)==h for path,h in bindings.items());ep=json.loads((base/'endpoints.json').read_text());graph,digest,nodes,f,rc,queries=load_endpoints(base/'endpoints.json');a=ImmutableXMLAudit(graph,digest);event=json.loads((R/'experiments/mcnc_bounded_owner_sequence_v1_2026-10-07/dsip/batch8.json').read_text());before={q['connection_id']:q for q in event['before_records']};release=set(event['released_net_ids']);rows=[]
for i,row in enumerate(r['rows']):
 file=out/f'policy{i}.json';assert sha(file)==row['candidate_sha256'];bindings[str(file)]=sha(file);c=json.loads(file.read_text());byid={q['connection_id']:q for q in c['records']};parents=defaultdict(dict)
 for cid,q in before.items():
  if q['net_id'] not in release:assert byid[cid]==q
 if row['committed']:assert set(byid)==set(before)|{event['query']['connection_id']}
 for rec in c['records']:
  assert rc.path(rec['source'],rec['sink'],rec['answer']['physical_edge_ids'])==rec['answer']['delay']<=rec['budget_integer'];u=rec['source']
  for eid in rec['answer']['physical_edge_ids']:
   edge=a.graph.edges[eid];assert edge.source==u;incoming=(u,eid);u=edge.sink;net=rec['net_id'];assert u not in parents[net] or parents[net][u]==incoming;parents[net][u]=incoming
 connections=[dict(q,method='searched' if q['connection_id'] in byid else 'failed',physical_edge_ids=byid[q['connection_id']]['answer']['physical_edge_ids'] if q['connection_id'] in byid else None) for q in queries];adapted=dict(connections=connections,physical_graph_sha256=digest,node_occupancy={str(k):v for k,v in c['ledger'].items()},methods=dict(Counter(q['method'] for q in connections)),completed=len(byid),requested=len(queries));audit=a.verify(ep,adapted);assert audit['all_physical_and_union_checks_passed'] and audit['all_type_overuse_units']==0;rows.append(dict(policy=row['policy'],committed=row['committed'],working_completed=len(byid),global_required=len(queries),unaffected_records_exact=True,audit=audit));print('PASS',i,flush=True)
assert all(sha(path)==h for path,h in bindings.items());(out/'verification.json').write_text(json.dumps(dict(rows=rows,bindings=bindings,scope='Post-outcome partial paths and batch reinsert proof; not full cohort or native validation.'),indent=2)+'\n')
