"""Evaluator-only exact native cohort audit and occupancy accuracy."""
from collections import Counter
import json,shutil
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from audit_native_route import audit
from native_node_labels import node_labels
from pin_template_trial import spatial
from prediction_metrics import compare
parent=Path('experiments/elliptic_transfer_2026-10-04');out=Path('experiments/elliptic_transfer_evaluation_2026-10-04')
if out.exists():raise ValueError('fresh output required')
r=json.loads((parent/'receipt.json').read_text());p=json.loads((parent/'protocol.json').read_text());assert r['protocol_sha256']==sha(parent/'protocol.json')
for f,digest in r['artifacts'].items():assert sha(parent/f)==digest
paths={'graph':Path(p['inputs']['graph']['path']),'endpoints':Path(p['inputs']['endpoints']['path']),'prediction':parent/'prediction.json','route':Path('work/elliptic_graph_capture_2026-10-04/elliptic.route'),'place':Path('work/elliptic_graph_capture_2026-10-04/elliptic.place')}
out.mkdir();(out/'source').mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
protocol={'scope':'additional same-architecture design, independent native cohort and occupancy evaluation, not feedback or speedup evidence','inputs':{k:{'path':str(v.resolve()),'sha256':sha(v)} for k,v in paths.items()},'source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')},'spatial_k':20,'resource_k':'floor5percent minimum1'}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');g=read_rr_graph(paths['graph']);e=json.loads(paths['endpoints'].read_text());pred=json.loads(paths['prediction'].read_text());native=audit(paths['graph'],paths['route']);truth=node_labels(g,paths['route'],sha(paths['place']))
key=lambda row:(row['net_id'],row['source'],row['sink'])
assert Counter(map(key,e['connections']))==Counter(map(key,native['connections']));assert not native['overflow_nodes']
resources=[n for n,node in g.nodes.items() if node.type in {'CHANX','CHANY'} and node.capacity];values=pred['node_occupancy']
result={'protocol_sha256':sha(out/'protocol.json'),'exact_native_endpoint_multiset':True,'native_connections':len(native['connections']),'native_overflow_nodes':0,'spatial':compare(spatial(g,values),spatial(g,truth),20),'resource':compare({str(n):values.get(str(n),0)/g.nodes[n].capacity for n in resources},{str(n):truth.get(str(n),0)/g.nodes[n].capacity for n in resources},max(1,len(resources)//20))}
(out/'native_audit.json').write_text(json.dumps(native)+'\n');(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
