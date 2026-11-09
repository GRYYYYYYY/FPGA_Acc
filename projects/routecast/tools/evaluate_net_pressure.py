"""Separate native-label comparison of frozen pressure and alpha-zero control."""
from pathlib import Path
import json,shutil
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from native_node_labels import node_labels
from pin_template_trial import spatial
from prediction_metrics import compare
out=Path('experiments/net_pressure_evaluation_2026-10-04');parent=Path('experiments/net_pressure_2026-10-04')
if out.exists():raise ValueError('fresh output required')
p=json.loads((parent/'protocol.json').read_text());r=json.loads((parent/'receipt.json').read_text());assert r['protocol_sha256']==sha(parent/'protocol.json')
for n,digest in r['artifacts'].items():assert sha(parent/n)==digest
route_d=Path(json.loads(Path('experiments/native_iteration_capture_2026-10-04/receipt.json').read_text())['final_route']['path']);routes={'diffeq':route_d,'elliptic':Path('work/elliptic_graph_capture_2026-10-04/elliptic.route')}
out.mkdir();(out/'source').mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
protocol={'scope':'known development own-net exclusion control; retain-own exact path control audited vs prior full pressure, no native quality/generalization claim','predictor_protocol_sha256':sha(parent/'protocol.json'),'labels':{n:{'route':str(r.resolve()),'route_sha256':sha(r),'place_sha256':sha(r.with_suffix('.place'))} for n,r in routes.items()},'spatial_k':20,'resource_k':'floor5percent min1','source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');results={}
for name,paths in p['inputs'].items():
    g=read_rr_graph(paths['graph']['path']);truth=node_labels(g,routes[name],sha(routes[name].with_suffix('.place')));resources=[n for n,v in g.nodes.items() if v.type in {'CHANX','CHANY'} and v.capacity];baseline=json.loads(Path(paths['background_prediction']['path']).read_text());retain=json.loads((parent/f'{name}_retain_own.json').read_text());exclude=json.loads((parent/f'{name}_exclude_own.json').read_text());prior=json.loads(Path(f'experiments/frozen_pressure_2026-10-04/{name}_prediction.json').read_text())
    identity=lambda pred:{r['connection_id']:(r['net_id'],r['source'],r['sink'],r['physical_edge_ids']) for r in pred['connections']}
    assert identity(retain)==identity(prior) and retain['node_occupancy']==prior['node_occupancy']
    variants={'hybrid_background':baseline,'retain_own':retain,'exclude_own':exclude};rows={}
    for variant,pred in variants.items():
        values=pred['node_occupancy'];rows[variant]={'spatial':compare(spatial(g,values),spatial(g,truth),20),'resource':compare({str(n):values.get(str(n),0)/g.nodes[n].capacity for n in resources},{str(n):truth.get(str(n),0)/g.nodes[n].capacity for n in resources},max(1,len(resources)//20)),'overflow_units':sum(max(0,v-g.nodes[int(n)].capacity) for n,v in values.items()),'overflow_nodes':sum(v>g.nodes[int(n)].capacity for n,v in values.items())}
    results[name]={'variants':rows,'retain_own_exact_prior_full_paths_and_union':True,'changed_exclusion_paths':sum(identity(retain)[cid]!=identity(exclude)[cid] for cid in identity(retain))};print(json.dumps({'design':name,'variants':rows}),flush=True)
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'results':results},indent=2)+'\n')
