"""Independent shortest-delay witness and edge-potential lower-bound certificate."""
import json
from pathlib import Path
from fractions import Fraction
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
root=Path(__file__).resolve().parents[1];out=root/'experiments/nonzero_rc_joint_failure_diagnosis_v2_2026-10-06';r=json.loads((out/'receipt.json').read_text());assert sha(root/'tools/diagnose_nonzero_rc_joint_failure_v2.py')==r['source_sha256'];graph=root/'work/nonzero_rc_fanout_observable64_2026-10-06/rr_graph.xml';audit=ImmutableXMLAudit(graph,r['graph_sha256']);ids,classes,switches,_=read(graph);q=r['failed_query'];scale=r['scale'];other={int(n):v for n,v in r['other_demand'].items()};checks=[]
for key,demand in [('capacity_minimum_delay',other),('unoccupied_minimum_delay',{})]:
 result=r[key];assert result['status']=='FOUND';potential={int(n):v for n,v in result['potential_integer'].items()};assert set(potential)==set(range(len(audit.caps)));initial=classes[ids[q['source']]][0]*classes[ids[q['source']]][1]/2;assert potential[q['source']]==initial*scale and potential[q['sink']]==result['delay_integer'];node=q['source'];used={node};delay=initial;assert demand.get(node,0)<audit.caps[node]
 for eid in result['physical_edge_ids']:
  edge=audit.graph.edges[eid];assert edge.source==node and edge.sink not in used;node=edge.sink;used.add(node);assert demand.get(node,0)<audit.caps[node];delay+=arc_delay(classes,switches,ids[node],edge.switch_id)
 assert node==q['sink'] and delay==Fraction(result['delay_integer'],scale)
 checked=0
 for eid in range(len(audit.graph.edges)):
  edge=audit.graph.edges[eid]
  if demand.get(edge.source,0)>=audit.caps[edge.source] or demand.get(edge.sink,0)>=audit.caps[edge.sink]:continue
  assert potential[edge.sink]<=potential[edge.source]+arc_delay(classes,switches,ids[edge.sink],edge.switch_id)*scale;checked+=1
 checks.append({'context':key,'exact_delay_ns':float(delay)*1e9,'admissible_edges_certified':checked})
assert r['capacity_minimum_delay']['delay_integer']>Fraction(1,10**9)*scale and r['unoccupied_minimum_delay']['delay_integer']<Fraction(1,10**9)*scale;assert r['native_trials']['1']['status']=='UNREACHABLE' and r['native_trials']['2']['status']=='FOUND'
(out/'verification.json').write_text(json.dumps({'checks':checks,'receipt_sha256':sha(out/'receipt.json'),'scope':'Original XML witness plus all admissible edge potential inequalities independently prove shortest delay in the frozen occupancy state. Capacity-constrained minimum exceeds1ns; graph is connected. No global layout infeasibility proof or relaxed-budget success claim.'},indent=2)+'\n');print(checks)
