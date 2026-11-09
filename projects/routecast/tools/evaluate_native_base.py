"""Native labels only in evaluator; fixed base cost vs prior physical length cost."""
import json,shutil
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from native_node_labels import node_labels
from pin_template_trial import spatial
from prediction_metrics import compare
parent=Path('experiments/native_base_cost_2026-10-04');out=Path('experiments/native_base_evaluation_2026-10-04')
if out.exists():raise ValueError('fresh output required')
p=json.loads((parent/'protocol.json').read_text());r=json.loads((parent/'receipt.json').read_text());assert r['protocol_sha256']==sha(parent/'protocol.json');assert r['prediction_sha256']==sha(parent/'prediction.json');route=Path(json.loads(Path('experiments/native_iteration_capture_2026-10-04/receipt.json').read_text())['final_route']['path']);baseline=Path('experiments/frozen_pressure_zero_2026-10-04/diffeq_prediction.json')
out.mkdir();(out/'source').mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
inputs={'native_base':parent/'prediction.json','length_switch':baseline,'route':route,'place':route.with_suffix('.place'),'graph':Path(p['inputs']['graph']['path'])};protocol={'scope':'single development design, base-cost-only full-path ablation, no per-connection timing or native routing equivalence','inputs':{k:{'path':str(v.resolve()),'sha256':sha(v)} for k,v in inputs.items()},'source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')},'spatial_k':20,'resource_k':'floor5percent minimum1'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');g=read_rr_graph(inputs['graph']);truth=node_labels(g,route,sha(inputs['place']));resources=[n for n,v in g.nodes.items() if v.type in {'CHANX','CHANY'} and v.capacity];rows={}
for name in ('length_switch','native_base'):
    pred=json.loads(inputs[name].read_text());assert pred['physical_graph_sha256']==g.sha256;values=pred['node_occupancy'];rows[name]={'spatial':compare(spatial(g,values),spatial(g,truth),20),'resource':compare({str(n):values.get(str(n),0)/g.nodes[n].capacity for n in resources},{str(n):truth.get(str(n),0)/g.nodes[n].capacity for n in resources},max(1,len(resources)//20)),'overflow_units':sum(max(0,v-g.nodes[int(n)].capacity) for n,v in values.items())}
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'rows':rows},indent=2)+'\n');print(json.dumps(rows))
