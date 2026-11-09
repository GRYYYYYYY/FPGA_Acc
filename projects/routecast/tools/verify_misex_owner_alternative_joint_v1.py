"""Independent partial XML audit and necessity minima for first joint conflict."""
import sys,json,heapq
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from immutable_xml_prediction_audit import ImmutableXMLAudit
out=R/'experiments/misex_owner_alternative_joint_v1_2026-10-07';base=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json');bindings={**p['inputs'],**p['sources'],**r['files'],**closure([Path(__file__)]),str(out/'receipt.json'):sha(out/'receipt.json')};assert all(sha(k)==v for k,v in bindings.items());(out/'verification_protocol.json').write_text(json.dumps(dict(bindings=bindings))+'\n');graph,digest,nodes,f,rc,queries=load_endpoints(base/'endpoints.json');ep=json.loads((base/'endpoints.json').read_text());a=ImmutableXMLAudit(graph,digest);rows=[]
for file in sorted(out.glob('branch*/net*.json'))+sorted(out.glob('branch*/joint_candidate.json')):
 c=json.loads(file.read_text());records={q['connection_id']:q for q in c['records']};parents=defaultdict(dict)
 for rec in c['records']:
  assert rc.path(rec['source'],rec['sink'],rec['answer']['physical_edge_ids'])==rec['answer']['delay']<=rec['budget_integer'];u=rec['source']
  for e in rec['answer']['physical_edge_ids']:
   edge=a.graph.edges[e];assert edge.source==u;incoming=(u,e);u=edge.sink;assert u not in parents[rec['net_id']] or parents[rec['net_id']][u]==incoming;parents[rec['net_id']][u]=incoming
 connections=[dict(q,method='searched' if q['connection_id'] in records else 'failed',physical_edge_ids=records[q['connection_id']]['answer']['physical_edge_ids'] if q['connection_id'] in records else None) for q in queries];adapted=dict(connections=connections,physical_graph_sha256=digest,node_occupancy={str(k):v for k,v in c['ledger'].items()},methods=dict(Counter(q['method'] for q in connections)),completed=len(records),requested=len(queries));audit=a.verify(ep,adapted);assert audit['all_physical_and_union_checks_passed'] and audit['all_type_overuse_units']==0;rows.append(dict(file=str(file),completed=len(records),xml_rc_parents_capacity_pass=True));print('PASS',file.name,file.parent.name,flush=True)
event=json.loads(Path(next(k for k in p['inputs'] if k.endswith('batch5.json'))).read_text());kept={x['connection_id']:x for x in event['before_records'] if x['net_id'] not in set(p['expanded_release'])};jointfiles=list(out.glob('branch*/joint_candidate.json'));assert r['joint_success'] and len(jointfiles)==1;state=json.loads(jointfiles[0].read_text());records={x['connection_id']:x for x in state['records']};assert state['required_connections']==2449 and len(records)==len(event['before_records'])+1 and set(records)=={x['connection_id'] for x in event['before_records']}|{event['query']['connection_id']};assert all(records[k]==v for k,v in kept.items())
for branch in r['branches']:
 for net,node in branch['constraints']:
  c=json.loads((out/f"branch{branch['index']}"/f'net{net}.json').read_text())
  for rec in c['records']:
   if rec['net_id']==net:
    assert rec['source']!=node
    assert all(a.graph.edges[e].sink!=node for e in rec['answer']['physical_edge_ids'])
cache=json.loads((out/'cache_receipt.json').read_text());assert cache['closed'] and not cache['invalid'] and cache['close_proof']['initial_and_final_content_digest_equal'];assert all(sha(k)==v for k,v in bindings.items());(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,states=rows,whole_released_nets_reinserted=True,unaffected_identity_exact=True,forbidden_nodes_respected=True,global_completed=len(records),global_required=2449,local_joint_only=True),indent=2)+'\n');print('PASS joint local full-reinsert',len(records),flush=True)
