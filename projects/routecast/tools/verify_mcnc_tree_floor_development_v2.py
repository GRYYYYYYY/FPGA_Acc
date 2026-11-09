"""Original XML path/owner/parent audits for every retained ablation outcome."""
import json,sys
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
base=R/'experiments/mcnc_prospective_v1_2026-10-07';out=R/'experiments/mcnc_tree_floor_development_v1_2026-10-07';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json');bindings={**p['inputs'],**p['sources'],**closure([Path(__file__)]),str(out/'receipt.json'):sha(out/'receipt.json')};assert all(sha(path)==h for path,h in bindings.items());(out/'verification_protocol_v2.json').write_text(json.dumps(dict(bindings=bindings,scope='All12 partial candidates, original individual arcs/NET union, all partial tree parents, capacity, budgets and root-vs-tree output parity. No complete native/predictor metrics.'),indent=2)+'\n');rows=[]
for name in p['cases']:
 ep=json.loads((base/name/'endpoints.json').read_text());graph,digest,nodes,fields,rc,queries=load_endpoints(base/name/'endpoints.json');a=ImmutableXMLAudit(Path(ep['inputs']['graph']['path']),ep['graph_sha256']);floorpath=out/(name+'_floors.json');floors={(q['source'],q['sink']):q['minimum_integer'] for q in json.loads(floorpath.read_text())};bindings[str(floorpath)]=sha(floorpath);results={}
 for row in [x for x in r['rows'] if x['name']==name]:
  file=Path(row['candidate_path']);assert sha(file)==row['candidate_sha256'];bindings[str(file)]=sha(file);c=json.loads(file.read_text());byid={v['connection_id']:v for v in c['records']};assert len(byid)==len(c['records']);connections=[dict(q,method='searched' if q['connection_id'] in byid else 'failed',physical_edge_ids=byid[q['connection_id']]['answer']['physical_edge_ids'] if q['connection_id'] in byid else None) for q in ep['connections']];methods=dict(Counter(q['method'] for q in connections));adapted=dict(connections=connections,physical_graph_sha256=c['graph_sha256'],node_occupancy={str(k):v for k,v in c['ledger'].items()},methods=methods,completed=c['completed_connections'],requested=c['required_connections']);audit=a.verify(ep,adapted);assert audit['all_physical_and_union_checks_passed'] and audit['all_type_overuse_units']==0
  parents=defaultdict(dict)
  for rec in c['records']:
   assert c['scale']==rc.scale and rc.path(rec['source'],rec['sink'],rec['answer']['physical_edge_ids'])==rec['answer']['delay'];u=rec['source'];initial=u
   for eid in rec['answer']['physical_edge_ids']:
    edge=a.graph.edges[eid];assert edge.source==u;parent=(u,eid);u=edge.sink;assert u not in parents[rec['net_id']] or parents[rec['net_id']][u]==parent;parents[rec['net_id']][u]=parent
   assert rec['floor_integer']==floors[rec['source'],rec['sink']];expected=max(c['scale']//10**9,(3*rec['floor_integer']+1)//2) if row['floor_budget'] else c['scale']//10**9;assert rec['budget_integer']==expected and rec['answer']['delay']<=expected
  results[row['tree'],row['floor_budget']]=c;rows.append(dict(name=name,tree=row['tree'],floor_budget=row['floor_budget'],completed=c['completed_connections'],required=c['required_connections'],failure=c['failure'],all_partial_tree_parents_compatible=True,original_xml_audit=audit));print('PASS',name,row['tree'],row['floor_budget'],flush=True)
 for budget in (False,True):
  aroot,atree=results[False,budget],results[True,budget]
  for key in ('records','ledger','completed_connections','required_connections','failure'):assert aroot[key]==atree[key],(name,budget,key)
assert all(sha(path)==h for path,h in bindings.items());(out/'verification_v2.json').write_text(json.dumps(dict(rows=rows,bindings=bindings,root_tree_records_ledger_failure_equal_all6_pairs=True,all_complete=all(x['completed']==x['required'] for x in rows)),indent=2)+'\n')
