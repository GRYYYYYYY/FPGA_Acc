"""Native-label-only evaluator for frozen larger-design transfer."""
from pathlib import Path
import json,shutil
from rr_graph import read_rr_graph
from pre_route_endpoints import sha
from native_node_labels import node_labels
from pin_template_trial import spatial
from prediction_metrics import compare
parent=Path('experiments/clma_normalized_transfer_2026-10-04');out=Path('experiments/clma_normalized_transfer_evaluation_2026-10-04')
if out.exists():raise ValueError('fresh output required')
p=json.loads((parent/'protocol.json').read_text());r=json.loads((parent/'receipt.json').read_text());assert r['protocol_sha256']==sha(parent/'protocol.json')
cap=json.loads(Path('experiments/clma_base_echo_2026-10-04/protocol.json').read_text())
inputs={'graph':p['inputs']['graph'],'route':cap['inputs']['route'],'place':cap['inputs']['place']}
for name,path in [('length_switch',Path('experiments/clma_cross_design_2026-10-04/raw.json')),('blend',parent/'blend_prediction.json'),('own_excluded_pressure',parent/'own_excluded_pressure_prediction.json')]:
 inputs[name]={'path':str(path.resolve()),'sha256':sha(path)}
 if name!='length_switch':assert r['stages'][name]['prediction_sha256']==sha(path)
assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
out.mkdir();(out/'source').mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
protocol={'inputs':inputs,'scope':'already-developed larger clma design, same architecture, native labels evaluator only; raw control occupancy archived (no stored full paths), new stages independently audited full paths','spatial_k':20,'resource_k':'floor5percent min1','source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');g=read_rr_graph(inputs['graph']['path']);truth=node_labels(g,inputs['route']['path'],inputs['place']['sha256']);resources=[n for n,v in g.nodes.items() if v.type in {'CHANX','CHANY'} and v.capacity];rows={}
for name in ('length_switch','blend','own_excluded_pressure'):
 pred=json.loads(Path(inputs[name]['path']).read_text());assert pred.get('physical_graph_sha256',pred.get('graph_sha256'))==g.sha256
 assert pred.get('completed',pred.get('connections_completed'))==13458
 values=pred['node_occupancy'];rows[name]={'spatial':compare(spatial(g,values),spatial(g,truth),20),'resource':compare({str(n):values.get(str(n),0)/g.nodes[n].capacity for n in resources},{str(n):truth.get(str(n),0)/g.nodes[n].capacity for n in resources},max(1,len(resources)//20)),'overflow_units':sum(max(0,v-g.nodes[int(n)].capacity) for n,v in values.items())}
assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'rows':rows,'inputs_unchanged':True},indent=2)+'\n');print(json.dumps(rows),flush=True)
