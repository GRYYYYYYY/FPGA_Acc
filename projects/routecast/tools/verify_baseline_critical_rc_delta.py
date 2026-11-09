import json
from pathlib import Path
from fractions import Fraction
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
root=Path(__file__).resolve().parents[1];out=root/'experiments/native_baseline_critical_rc_delta_2026-10-06';receipt=json.loads((out/'receipt.json').read_text());protocol=json.loads((out/'protocol.json').read_text());assert sha(out/'protocol.json')==receipt['protocol_sha256'] and sha(out/'results.json')==receipt['results_sha256'];q=root/'experiments/native_baseline_critical_rr_pin_2026-10-06/queries.json';assert sha(q)==protocol['queries_sha256'];mapping=json.loads(q.read_text());graph=Path(next(p for p in mapping['inputs_sha256'] if p.endswith('rr_graph.xml')));audit=ImmutableXMLAudit(graph,protocol['graph_sha256']);ids,classes,switches,digest=read(graph);rows=json.loads((out/'results.json').read_text())['results'];assert len(rows)==126;seen=set()
for row in rows:
 r=row['result'];assert r['status']=='FOUND';node=row['source'];res,cap=classes[ids[node]];delay=res*cap/2;visited={node}
 for eid in r['physical_edge_ids']:
  e=audit.graph.edges[eid];assert e.source==node and e.sink not in visited;node=e.sink;visited.add(node);delay+=arc_delay(classes,switches,ids[node],e.switch_id)
 assert node==row['sink'] and delay==Fraction(r['delay'],protocol['scale']) and delay<=Fraction(1,10**9);seen.add((row['source'],row['sink']))
(out/'verification.json').write_text(json.dumps({'rows':126,'unique_paths':len(seen),'graph_sha256':digest,'results_sha256':sha(out/'results.json'),'checks':['original XML edge source/destination/switch witness continuity','original XML exact buffered RC path delay equality to native integer result','fixed 1ns budget compliance'],'scope':'Isolated connection expansion delay and path witness, zero other-NET demand; not multi-NET overflow, route-tree branching load, optimal delay, full critical-path STA or native timing guarantee.'},indent=2)+'\n');print('verified',len(rows),'RC paths')
