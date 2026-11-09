"""Native labels evaluator only; RC-only versus physical length+switch control."""
import json,shutil
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from native_node_labels import node_labels
from pin_template_trial import spatial
from prediction_metrics import compare
parent=Path('experiments/normalized_rc_pressure_search_2026-10-04');out=Path('experiments/normalized_rc_pressure_evaluation_2026-10-04')
if out.exists():raise ValueError('fresh output required')
p=json.loads((parent/'protocol.json').read_text());receipt=json.loads((parent/'receipt.json').read_text());assert receipt['protocol_sha256']==sha(parent/'protocol.json')
inputs={}
for design,folder in [('diffeq','baseline_cluster_criticality_v7_2026-10-04'),('elliptic','elliptic_cluster_criticality_v7_2026-10-04')]:
 cap=json.loads((Path('experiments')/folder/'protocol.json').read_text());route=Path(cap['inputs']['route']['path'])
 paths={'rc_base':Path('experiments/normalized_rc_base_search_2026-10-04')/f'{design}_prediction.json','rc_only':Path('experiments/buffered_rc_search_2026-10-04')/f'{design}_prediction.json','rc_pressure':parent/f'{design}_prediction.json','length_switch':Path('experiments/frozen_pressure_zero_2026-10-04')/f'{design}_prediction.json','route':route,'place':route.with_suffix('.place'),'graph':Path(p['inputs'][design]['graph']['path'])}
 assert receipt['designs'][design]['prediction_sha256']==sha(paths['rc_pressure'])
 inputs[design]={k:{'path':str(v.resolve()),'sha256':sha(v)} for k,v in paths.items()}
out.mkdir();(out/'source').mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
(out/'protocol.json').write_text(json.dumps({'inputs':inputs,'spatial_k':20,'resource_k':'floor5percent min1','scope':'same-architecture two-design development evaluation; native route labels never consumed by RC predictor','source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}},indent=2)+'\n')
rows={}
for design,paths in inputs.items():
 g=read_rr_graph(paths['graph']['path']);truth=node_labels(g,paths['route']['path'],paths['place']['sha256']);resources=[n for n,v in g.nodes.items() if v.type in {'CHANX','CHANY'} and v.capacity];rows[design]={}
 for name in ('length_switch','rc_only','rc_base','rc_pressure'):
  pred=json.loads(Path(paths[name]['path']).read_text());assert pred['physical_graph_sha256']==g.sha256;values=pred['node_occupancy']
  rows[design][name]={'spatial':compare(spatial(g,values),spatial(g,truth),20),'resource':compare({str(n):values.get(str(n),0)/g.nodes[n].capacity for n in resources},{str(n):truth.get(str(n),0)/g.nodes[n].capacity for n in resources},max(1,len(resources)//20)),'overflow_units':sum(max(0,v-g.nodes[int(n)].capacity) for n,v in values.items())}
assert all(sha(v['path'])==v['sha256'] for group in inputs.values() for v in group.values())
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'inputs_unchanged':True,'rows':rows},indent=2)+'\n');print(json.dumps(rows))
