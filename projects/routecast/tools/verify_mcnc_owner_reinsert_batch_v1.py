"""Full partial-cohort audit and honest scoped publication of local batch commits."""
import json,sys
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from immutable_xml_prediction_audit import ImmutableXMLAudit
base=R/'experiments/mcnc_prospective_v1_2026-10-07';dev=R/'experiments/mcnc_tree_floor_development_v1_2026-10-07';out=R/'experiments/mcnc_owner_reinsert_batch_v1_2026-10-07';r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json');bindings={**p['inputs'],**p['sources'],**closure([Path(__file__)]),str(out/'receipt.json'):sha(out/'receipt.json')};assert all(sha(path)==h for path,h in bindings.items());(out/'verification_protocol.json').write_text(json.dumps(dict(bindings=bindings,scope='Commit includes every released connection, unaffected records unchanged, whole partial-cohort XML/RC/parents/capacity audit. Publish global requested count/pending IDs; helper status COMPLETE refers only to finite local batch, not full cohort or native routing.'),indent=2)+'\n');rows=[]
for row in r['rows']:
 name=row['name'];assert all(sha(path)==h for path,h in row['files'].items());bindings.update(row['files']);w=out/name;original=json.loads((dev/f'{name}_tree1_floor1.json').read_text());c=json.loads((w/'accepted.json').read_text());ep=json.loads((base/name/'endpoints.json').read_text());graph,digest,nodes,f,rc,queries=load_endpoints(base/name/'endpoints.json');a=ImmutableXMLAudit(graph,digest);byid={q['connection_id']:q for q in c['records']};before={q['connection_id']:q for q in original['records']};expected=set(before)|{row['batch_queries'][0]['connection_id']} if row['committed'] else set(before);assert set(byid)==expected
 for cid,rec in before.items():
  if rec['net_id'] not in row['released_net_ids']:assert byid[cid]==rec
  elif row['committed']:assert cid in byid
 if not row['committed']:assert c==original
 parents=defaultdict(dict)
 for rec in c['records']:
  assert rc.path(rec['source'],rec['sink'],rec['answer']['physical_edge_ids'])==rec['answer']['delay']<=rec['budget_integer'];u=rec['source']
  for eid in rec['answer']['physical_edge_ids']:
   edge=a.graph.edges[eid];assert edge.source==u;incoming=(u,eid);u=edge.sink;net=rec['net_id'];assert u not in parents[net] or parents[net][u]==incoming;parents[net][u]=incoming
 connections=[dict(q,method='searched' if q['connection_id'] in byid else 'failed',physical_edge_ids=byid[q['connection_id']]['answer']['physical_edge_ids'] if q['connection_id'] in byid else None) for q in queries];adapted=dict(connections=connections,physical_graph_sha256=digest,node_occupancy={str(k):v for k,v in c['ledger'].items()},methods=dict(Counter(q['method'] for q in connections)),completed=len(byid),requested=len(queries));audit=a.verify(ep,adapted);assert audit['all_physical_and_union_checks_passed'] and audit['all_type_overuse_units']==0
 pending=sorted({q['connection_id'] for q in queries}-set(byid));scoped={**c,'status':'INCOMPLETE_NOT_PUBLISHABLE' if pending else 'COMPLETE_DIAGNOSTIC','required_connections':len(queries),'pending_connection_ids':pending,'scope':'Local owner-release/reinsert commit only. Pending full cohort explicit; no native pin/route/STA acceptance or total QoR claim.'};file=w/'accepted_scoped.json';file.write_text(json.dumps(scoped)+'\n');rows.append(dict(name=name,committed=row['committed'],all_released_connections_reinserted=row['committed'],unaffected_records_exact=True,completed=len(byid),required=len(queries),pending=len(pending),audit=audit,scoped_candidate_sha256=sha(file)));print('PASS',name,len(byid),len(queries),flush=True)
assert all(sha(path)==h for path,h in bindings.items());(out/'verification.json').write_text(json.dumps(dict(rows=rows,bindings=bindings,all_full_cohorts_complete=all(row['pending']==0 for row in rows)),indent=2)+'\n')
