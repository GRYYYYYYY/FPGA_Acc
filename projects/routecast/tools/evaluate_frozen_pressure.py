"""Separate native-label comparison of frozen pressure and alpha-zero control."""
from pathlib import Path
import json,shutil
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from native_node_labels import node_labels
from pin_template_trial import spatial
from prediction_metrics import compare
out=Path('experiments/frozen_pressure_evaluation_2026-10-04');parent=Path('experiments/frozen_pressure_2026-10-04');zero=Path('experiments/frozen_pressure_zero_2026-10-04')
if out.exists():raise ValueError('fresh output required')
p=json.loads((parent/'protocol.json').read_text());z=json.loads((zero/'protocol.json').read_text());assert p['inputs']==z['inputs'];assert p['source_sha256']['frozen_pressure_sketch.py']==z['source_sha256']['frozen_pressure_sketch.py']
for root in (parent,zero):
    r=json.loads((root/'receipt.json').read_text());assert sha(root/'protocol.json')==r['protocol_sha256']
    for n,digest in r['prediction_sha256'].items():assert sha(root/f'{n}_prediction.json')==digest
route_d=Path(json.loads(Path('experiments/native_iteration_capture_2026-10-04/receipt.json').read_text())['final_route']['path']);routes={'diffeq':route_d,'elliptic':Path('work/elliptic_graph_capture_2026-10-04/elliptic.route')}
out.mkdir();(out/'source').mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
protocol={'scope':'known development design accuracy; isolates alpha0 vs256 same physical search; no native feedback or generalized claim','predictor_protocols':{'zero':sha(zero/'protocol.json'),'pressure':sha(parent/'protocol.json')},'labels':{n:{'route':str(r.resolve()),'route_sha256':sha(r),'place_sha256':sha(r.with_suffix('.place'))} for n,r in routes.items()},'spatial_k':20,'resource_k':'floor5percent min1','source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');results={}
for name,paths in p['inputs'].items():
    g=read_rr_graph(paths['graph']['path']);truth=node_labels(g,routes[name],sha(routes[name].with_suffix('.place')));resources=[n for n,v in g.nodes.items() if v.type in {'CHANX','CHANY'} and v.capacity];baseline=json.loads(Path(paths['background_prediction']['path']).read_text());variants={'hybrid_background':baseline,'zero':json.loads((zero/f'{name}_prediction.json').read_text()),'pressure':json.loads((parent/f'{name}_prediction.json').read_text())};rows={}
    for variant,pred in variants.items():
        values=pred['node_occupancy'];rows[variant]={'spatial':compare(spatial(g,values),spatial(g,truth),20),'resource':compare({str(n):values.get(str(n),0)/g.nodes[n].capacity for n in resources},{str(n):truth.get(str(n),0)/g.nodes[n].capacity for n in resources},max(1,len(resources)//20)),'overflow_units':sum(max(0,v-g.nodes[int(n)].capacity) for n,v in values.items()),'overflow_nodes':sum(v>g.nodes[int(n)].capacity for n,v in values.items())}
    results[name]=rows;print(json.dumps({'design':name,'variants':rows}),flush=True)
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'results':results},indent=2)+'\n')
