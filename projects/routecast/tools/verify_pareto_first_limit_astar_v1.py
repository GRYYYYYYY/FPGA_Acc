"""Independent heuristic certificate and full partial-state XML/RC replay."""
import json,sys
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from immutable_xml_prediction_audit import ImmutableXMLAudit
base=R/'experiments/mcnc_prospective_v1_2026-10-07';parent=R/'experiments/mcnc_bounded_owner_pareto_v3_2026-10-07';out=R/'experiments/pareto_first_limit_astar_v1_2026-10-07';r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json');bindings={**p['inputs'],**p['sources'],**closure([Path(__file__)]),str(out/'receipt.json'):sha(out/'receipt.json')};assert all(sha(path)==h for path,h in bindings.items());(out/'verification_protocol.json').write_text(json.dumps(dict(bindings=bindings,scope='All positive-capacity arc lower-bound inequality/domain closure, target zero; all old+new partial routes/owners/parents/exact delays and immutable earlier records. Not complete routing or STA.'))+'\n');rows=[]
for row in r['rows']:
 name=row['name'];assert all(sha(path)==h for path,h in row['files'].items());bindings.update(row['files']);ep=json.loads((base/name/'endpoints.json').read_text());graph,digest,nodes,f,rc,queries=load_endpoints(base/name/'endpoints.json');a=ImmutableXMLAudit(graph,digest);rem={int(n):d for n,d in json.loads((out/name/'remaining_delay.json').read_text()).items()};assert rem[row['query']['sink']]==0 and all(d>=0 for d in rem.values());checked=0
 for u in range(len(nodes)):
  for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   v=f['dest_ranks'][s]
   if f['capacities'][u]>0 and v in rem:assert u in rem and rem[u]<=rc.increments[s]+rem[v];checked+=1
 original=json.loads((parent/name/'candidate.json').read_text());before={r['connection_id']:r for r in original['records']};case=[]
 for kind in ('baseline','astar'):
  c=json.loads((out/name/(kind+'.json')).read_text());byid={r['connection_id']:r for r in c['records']};expected=set(before)|{row['query']['connection_id']} if c['failure'] is None else set(before);assert set(byid)==expected
  for cid,rec in before.items():assert byid[cid]==rec
  parents=defaultdict(dict)
  for rec in c['records']:
   assert rc.path(rec['source'],rec['sink'],rec['answer']['physical_edge_ids'])==rec['answer']['delay']<=rec['budget_integer'];u=rec['source']
   for eid in rec['answer']['physical_edge_ids']:
    edge=a.graph.edges[eid];assert edge.source==u;incoming=(u,eid);u=edge.sink;net=rec['net_id'];assert u not in parents[net] or parents[net][u]==incoming;parents[net][u]=incoming
  connections=[dict(q,method='searched' if q['connection_id'] in byid else 'failed',physical_edge_ids=byid[q['connection_id']]['answer']['physical_edge_ids'] if q['connection_id'] in byid else None) for q in queries];adapted=dict(connections=connections,physical_graph_sha256=digest,node_occupancy={str(k):v for k,v in c['ledger'].items()},methods=dict(Counter(q['method'] for q in connections)),completed=len(byid),requested=len(queries));audit=a.verify(ep,adapted);assert audit['all_physical_and_union_checks_passed'] and audit['all_type_overuse_units']==0;case.append(dict(kind=kind,completed=len(byid),global_required=len(queries),audit=audit,earlier_records_exact=True))
 rows.append(dict(name=name,heuristic_inequality_arcs_checked=checked,heuristic_admissibility_certificate_pass=True,states=case));print('PASS',name,flush=True)
assert all(sha(path)==h for path,h in bindings.items());(out/'verification.json').write_text(json.dumps(dict(rows=rows,bindings=bindings),indent=2)+'\n')
