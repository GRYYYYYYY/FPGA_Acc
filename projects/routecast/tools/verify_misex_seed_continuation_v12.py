"""Independent XML, additive RC, tree, seed preservation and complete scope audit."""
import sys,json
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from immutable_xml_prediction_audit import ImmutableXMLAudit
out=R/'experiments/misex_verified_seed_continuation_v12_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());bindings={**r['bindings'],**r['files'],**closure([Path(__file__)]),str(rp):sha(rp)};assert all(sha(k)==v for k,v in bindings.items());ep=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json';graph,digest,nodes,f,rc,queries=load_endpoints(ep);audit=ImmutableXMLAudit(graph,digest);state=json.loads((out/'candidate.json').read_text());records={x['connection_id']:x for x in state['records']};assert len(records)==len(state['records']);querymap={q['connection_id']:q for q in queries};parents=defaultdict(dict)
for cid,rec in records.items():
 assert all(rec[k]==querymap[cid][k] for k in ('net_id','source','sink'));assert rc.path(rec['source'],rec['sink'],rec['answer']['physical_edge_ids'])==rec['answer']['delay']<=rec['budget_integer'];u=rec['source']
 for edge in rec['answer']['physical_edge_ids']:
  arc=audit.graph.edges[edge];assert arc.source==u;incoming=(u,edge);u=arc.sink;assert u not in parents[rec['net_id']] or parents[rec['net_id']][u]==incoming;parents[rec['net_id']][u]=incoming
seed=json.loads((R/'experiments/misex_window_witness_guided_joint_v8_2026-10-07/candidate.json').read_text());assert all(records[x['connection_id']]==x for x in seed['records']);assert state['pending_connection_ids']==sorted(querymap.keys()-records.keys());assert state['required_connections']==r['required']==len(queries) and state['completed_connections']==r['completed']==len(records);connections=[dict(q,method='searched' if q['connection_id'] in records else 'failed',physical_edge_ids=records[q['connection_id']]['answer']['physical_edge_ids'] if q['connection_id'] in records else None) for q in queries];adapted=dict(connections=connections,physical_graph_sha256=digest,node_occupancy={str(k):v for k,v in state['ledger'].items()},methods=dict(Counter(q['method'] for q in connections)),completed=len(records),requested=len(queries));proof=audit.verify(json.loads(ep.read_text()),adapted);assert proof['all_physical_and_union_checks_passed'] and proof['all_type_overuse_units']==0;assert all(sha(k)==v for k,v in bindings.items());(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,completed=len(records),required=len(queries),all_seed_xml_rc_tree_capacity_and_scope_checks_pass=True),indent=2)+'\n');print('PASS continuation',len(records),len(queries))
