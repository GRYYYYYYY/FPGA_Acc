import json,sys,time,xml.etree.ElementTree as E
from pathlib import Path
from types import SimpleNamespace
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from endpoint_bbox_demand_v1 import predict
src=Path(sys.argv[1]).resolve();epfile=src/'endpoints.json';proof=src/'verification.json';d=json.loads(proof.read_text());assert d['exhaustive_disjoint_partition_exact_original_queries_and_whole_NET_scope_pass'] and all(sha(k)==v for k,v in d['bindings'].items());ep=json.loads(epfile.read_text());graph=Path(ep['inputs']['graph']['path']);protocol=R/'experiments/ultraembedded_prospective_evaluation_prereg_v1_2026-10-08/protocol.json';pr=json.loads(protocol.read_text());assert all(sha(k)==v for k,v in pr['bindings'].items());out=Path(sys.argv[2]).resolve();out.mkdir(parents=True);bindings={str(p):sha(p) for p in [Path(__file__),R/'tools/endpoint_bbox_demand_v1.py',epfile,proof,graph,protocol]};assert sha(graph)==ep['graph_sha256'];tick=time.perf_counter();nodes={};stack=[]
for event,el in E.iterparse(graph,events=('start','end')):
 if event=='start':stack.append(el);continue
 if el.tag=='node':
  n=int(el.get('id'));assert n not in nodes;segment=el.find('segment');nodes[n]=SimpleNamespace(type=el.get('type'),capacity=int(el.get('capacity')),location=tuple(el.find('loc').attrib.items()),segment_id=int(segment.get('segment_id')) if segment is not None else None)
 if el.tag in {'node','edge'}:
  if len(stack)>1:stack[-2].remove(el)
  el.clear()
 stack.pop()
assert all(q['source'] in nodes and q['sink'] in nodes for q in ep['connections']);values,capacities=predict(nodes,ep['connections']);assert set(values)==set(capacities);p=out/'prediction.json';p.write_text(json.dumps(dict(required_queries=len(ep['connections']),all_nodes=len(nodes),bins=[dict(key=list(k),capacity=capacities[k],geometry=values[k]) for k in sorted(values)],scope='Unfitted perNET directional bbox/capacity, all physical endpoints. No path, budget/route legality or native labels.' ))+'\n');assert all(sha(k)==v for k,v in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,prediction_sha256=sha(p),process_internal_seconds=time.perf_counter()-tick,physical_connections=len(ep['connections']),spatial_bins=len(values),native_labels_used=False),indent=2)+'\n');print('GEOMETRY',len(ep['connections']),len(values),flush=True)
