"""Independent XML path and all-edge lower-bound certificates for65 queries."""
import json
from pathlib import Path
from fractions import Fraction
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
root=Path(__file__).resolve().parents[1];out=root/'experiments/nonzero_rc_ex5p_label_diagnosis_2026-10-06';r=json.loads((out/'receipt.json').read_text());parent=root/'experiments/nonzero_rc_ex5p_independent_prediction_2026-10-06/receipt.json';prior=json.loads(parent.read_text());assert r['parent_sha256']==sha(parent) and r['protocol_sha256']==sha(out/'protocol.json') and r['source_sha256']==sha(root/'tools/diagnose_nonzero_rc_ex5p_label_limits.py');ep=root/'experiments/nonzero_rc_ex5p_endpoints_2026-10-06/endpoints.json';assert r['endpoint_sha256']==sha(ep);endpoints=json.loads(ep.read_text());graph=Path(endpoints['inputs']['graph']['path']);audit=ImmutableXMLAudit(graph,r['graph_sha256']);ids,classes,switches,_=read(graph);scale=r['scale'];assert r['budget_integer']==prior['budget_integer']==scale//10**9;expected={q['connection_id']:q for q in prior['records'] if q['answer']['status']=='LABEL_LIMIT'};edges=[]
for eid in range(len(audit.graph.edges)):
 e=audit.graph.edges[eid];increment=arc_delay(classes,switches,ids[e.sink],e.switch_id)*scale;assert increment.denominator==1;edges.append((e.source,e.sink,int(increment)))
seen=set();edge_checks=0;maxdelay=Fraction(0)
for record in r['records']:
 q=record['query'];cid=q['connection_id'];assert cid in expected and cid not in seen and q=={k:v for k,v in expected[cid].items() if k!='answer'};seen.add(cid);potential=record['potential_integer'];assert len(potential)==len(audit.caps) and all(type(x) is int and x>=0 for x in potential);node=q['source'];used={node};res,cap=classes[ids[node]];delay=res*cap/2;assert potential[node]==delay*scale and audit.caps[node]>0
 for eid in record['physical_edge_ids']:
  u,dst,increment=edges[eid];assert u==node and dst not in used and audit.caps[dst]>0;node=dst;used.add(node);delay+=Fraction(increment,scale)
 assert node==q['sink'] and delay*scale==record['delay_integer']==potential[node];assert record['within_original_budget']==(delay<=Fraction(1,10**9));maxdelay=max(maxdelay,delay)
 for u,dst,increment in edges:
  if audit.caps[u]==0 or audit.caps[dst]==0:continue
  assert potential[dst]<=potential[u]+increment;edge_checks+=1
assert seen==set(expected) and len(seen)==65 and all(q['within_original_budget'] for q in r['records']);(out/'verification.json').write_text(json.dumps({'queries_checked':65,'within1ns':65,'admissible_edge_inequalities_checked':edge_checks,'max_certified_minimum_delay_ns':float(maxdelay)*1e9,'receipt_sha256':sha(out/'receipt.json'),'scope':'Every frozen label-limit query has exact originalXML simplepath <=1ns; clipped potentials satisfy every capacity-admissible edge and prove minimum delay. Empty demand diagnosis only, not unit-edge objective optimality, complete joint capacity/nativeFULL/STA or net benefit.'},indent=2)+'\n');print('verified65 minimum-delay certificates; edge inequalities',edge_checks,'max ns',float(maxdelay)*1e9)
