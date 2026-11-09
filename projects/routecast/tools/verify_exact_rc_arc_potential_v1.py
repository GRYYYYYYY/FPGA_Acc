"""Independent original XML/Fraction verification of potential or contradiction."""
import json,sys
from pathlib import Path
from fractions import Fraction
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
name=sys.argv[1];D=R/'experiments/exact_rc_arc_potential_v1_2026-10-08'/name
def load(p):return json.loads(p.read_text())
r=load(D/'receipt.json');p=load(D/'protocol.json')
for d in [r,p]:
 for section in ['bindings','files']:
  for path,h in d.get(section,{}).items():assert sha(path)==h,path
assert r['bindings']==p['bindings']
ep=load(next(Path(k) for k in r['bindings'] if k.endswith('/endpoints.json')))
graph=Path(ep['inputs']['graph']['path']);xml=ImmutableXMLAudit(graph,p['graph_sha256']);ids,classes,switches,digest=read(graph)
assert digest==p['graph_sha256'];scale=p['scale'];assert isinstance(scale,int) and scale>0
def cost(eid):
 e=xml.graph.edges[eid];assert xml.graph.nodes[e.source].capacity>0 and xml.graph.nodes[e.sink].capacity>0
 return e,arc_delay(classes,switches,ids[e.sink],e.switch_id)
result=r['result'];status=result['status']
if status=='POTENTIAL_CONTRADICTION':
 c=result['conflict'];edge,value=cost(c['physical_edge_id'])
 assert (edge.source,edge.sink)==(c['source'],c['sink'])
 assert value==Fraction(c['increment_integer'],scale)
 u=c['source'];summed=Fraction(0);seen={u}
 for step in c['algebraic_forest_path']:
  e,increment=cost(step['physical_edge_id']);direction=step['direction'];assert direction in [-1,1]
  a,b=(e.source,e.sink) if direction==1 else (e.sink,e.source)
  assert (step['source'],step['sink'])==(a,b) and a==u and b not in seen
  summed+=direction*increment;u=b;seen.add(u)
 assert u==c['sink'] and summed==Fraction(c['forest_implied_increment_integer'],scale) and summed!=value
 proof=dict(original_XML_fraction_algebraic_contradiction_pass=True,all_positive_capacity_arcs_potential_pass=False,witness_forest_edges=len(c['algebraic_forest_path']),actual_arc_fraction_s=str(value),forest_implied_fraction_s=str(summed),scope='Nonzero signed algebraic cycle proves no global node potential can satisfy all positive-capacity arc RC equations. Forest reverse traversal is algebra, not a legal route or proof of cost variation for a particular endpoint query.')
elif status=='ALL_POSITIVE_CAPACITY_ARCS_POTENTIAL_PASS':
 data=load(D/'potential.json');potential=data['potential'];components=data['components']
 assert len(potential)==len(components)==len(ids)==result['original_nodes']
 assert len(xml.graph.edges)==result['original_arcs'];checked=0
 for eid in range(len(xml.graph.edges)):
  e=xml.graph.edges[eid]
  if not xml.graph.nodes[e.source].capacity or not xml.graph.nodes[e.sink].capacity:continue
  _,value=cost(eid);assert components[e.source]==components[e.sink]
  assert Fraction(potential[e.sink]-potential[e.source],scale)==value;checked+=1
 assert checked==result['checked_arcs']
 queries={q['connection_id']:q for q in ep['connections']};rows=load(D/'query_delays.json')
 assert len(rows)==len(queries)==result['queries'] and {q['connection_id'] for q in rows}==set(queries)
 for row in rows:
  q=queries[row['connection_id']];source=q['source'];sink=q['sink']
  assert (row['source'],row['sink'])==(source,sink) and components[source]==components[sink]
  a,b=classes[ids[source]];delay=a*b/2+Fraction(potential[sink]-potential[source],scale)
  assert delay==Fraction(row['endpoint_path_delay_integer'],scale)>=0
 proof=dict(all_positive_capacity_arcs_potential_pass=True,original_XML_fraction_all_arc_equations_pass=True,checked_arcs=checked,queries=len(rows),scope='Every valid positive-capacity path telescopes; same component alone does not prove directed endpoint reachability, weighted-feedback simplification, route legality or physical characterized timing.')
else:raise AssertionError(status)
bindings={**r['bindings'],**r['files'],str(D/'receipt.json'):sha(D/'receipt.json'),str(Path(__file__)):sha(Path(__file__))}
assert all(sha(k)==h for k,h in bindings.items())
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,status=status,**proof),indent=2)+'\n')
print(json.dumps(proof,indent=2))
