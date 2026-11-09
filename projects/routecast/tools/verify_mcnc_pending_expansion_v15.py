"""Final whole partial-cohort audits plus every batch's all-or-nothing identity."""
import json,sys
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from immutable_xml_prediction_audit import ImmutableXMLAudit
base=R/'experiments/mcnc_prospective_v1_2026-10-07';out=R/'experiments/mcnc_pending_expansion_v15_2026-10-07';r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json');bindings={**p['inputs'],**p['sources'],**closure([Path(__file__)]),str(out/'receipt.json'):sha(out/'receipt.json')};assert all(sha(path)==h for path,h in bindings.items());(out/'verification_protocol.json').write_text(json.dumps(dict(bindings=bindings))+'\n');rows=[]
for row in r['rows']:
 name=row['name'];assert all(sha(path)==h for path,h in row['files'].items());bindings.update(row['files']);ep=json.loads((base/name/'endpoints.json').read_text());graph,digest,nodes,f,rc,queries=load_endpoints(base/name/'endpoints.json');a=ImmutableXMLAudit(graph,digest);c=json.loads((out/name/'candidate.json').read_text());byid={q['connection_id']:q for q in c['records']};parents=defaultdict(dict)
 assert len(byid)==len(c['records']);querymap={q['connection_id']:q for q in queries}
 for rec in c['records']:
  assert all(rec[k]==querymap[rec['connection_id']][k] for k in ('net_id','source','sink'))
  assert rc.path(rec['source'],rec['sink'],rec['answer']['physical_edge_ids'])==rec['answer']['delay']<=rec['budget_integer'];u=rec['source']
  for eid in rec['answer']['physical_edge_ids']:
   edge=a.graph.edges[eid];assert edge.source==u;incoming=(u,eid);u=edge.sink;assert u not in parents[rec['net_id']] or parents[rec['net_id']][u]==incoming;parents[rec['net_id']][u]=incoming
 connections=[dict(q,method='searched' if q['connection_id'] in byid else 'failed',physical_edge_ids=byid[q['connection_id']]['answer']['physical_edge_ids'] if q['connection_id'] in byid else None) for q in queries];adapted=dict(connections=connections,physical_graph_sha256=digest,node_occupancy={str(k):v for k,v in c['ledger'].items()},methods=dict(Counter(q['method'] for q in connections)),completed=len(byid),requested=len(queries));audit=a.verify(ep,adapted);assert audit['all_physical_and_union_checks_passed'] and audit['all_type_overuse_units']==0;assert c['required_connections']==len(queries) and c['pending_connection_ids']==sorted({q['connection_id'] for q in queries}-set(byid))
 for i in range(1,row['batches']+1):
  event=json.loads((out/name/f'batch{i}.json').read_text());before={q['connection_id']:q for q in event['before_records']};working={q['connection_id']:q for q in event['working_records']};removed=set(event['removed_connection_ids']);release=set(event['released_net_ids']);assert len(release)<=4 and len(event['selection']['queries'])<=16;assert set(event['selection']['removed_connection_ids'])=={cid for cid,q in before.items() if q['net_id'] in event['initial_release_net_ids']};assert removed=={cid for cid,q in before.items() if q['net_id'] in release}
  for cid,q in before.items():
   if cid not in removed:assert working[cid]==q
  if event['committed']:assert event['batch_failure'] is None and set(working)==set(before)|set(event['selection']['requested_connection_ids'])
  elif row['stop']=='BATCH_ROLLBACK':assert c['records']==event['before_records'] and c['ledger']==event['before_ledger']
 rows.append(dict(name=name,completed=len(byid),required=len(queries),stop=row['stop'],batches=row['batches'],commits=row['commits'],audit=audit,all_partial_parents_and_exact_delays_pass=True,batch_unaffected_and_reinsert_identity_pass=True));print('PASS',name,len(byid),flush=True)
assert all(sha(path)==h for path,h in bindings.items());(out/'verification.json').write_text(json.dumps(dict(rows=rows,bindings=bindings),indent=2)+'\n')
