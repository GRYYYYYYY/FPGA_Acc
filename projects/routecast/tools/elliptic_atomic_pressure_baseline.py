"""One deterministic development net, full physical own-excluded pressure search."""
import json,shutil,time
from pathlib import Path
from pre_route_endpoints import sha
from prepared_endpoints import PreparedEndpoints
from rr_graph import read_rr_graph
from atomic_pressure_recompute import recompute
from feedback_scores import scores
out=Path('experiments/elliptic_atomic_pressure_baseline_2026-10-05')
if out.exists():raise ValueError('fresh output required')
out.mkdir();(out/'source').mkdir()
for f in Path('tools').glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
epath=Path('experiments/elliptic_endpoints_2026-10-04/endpoints.json');e=json.loads(epath.read_text());place=Path(e['inputs']['place']['path']);pfile=Path('experiments/elliptic_sketch_neighborhood_2026-10-05/baseline_prediction.json');cfile=Path('experiments/elliptic_sketch_neighborhood_2026-10-05/closure_0.json')
inputs={str(p):sha(p) for p in (epath,place,pfile,cfile)};inputs.update({v['path']:v['sha256'] for v in e['inputs'].values()});assert all(sha(p)==h for p,h in inputs.items())
t=time.monotonic();g=read_rr_graph(e['inputs']['graph']['path']);frontend=PreparedEndpoints(e['inputs']['net']['path'],e['inputs']['graph']['path'],e['inputs']['place']['path']);after,_=frontend.project(place);background=json.loads(pfile.read_text());closure=json.loads(cfile.read_text());groups={}
for r in after['connections']:groups.setdefault(r['net_id'],[]).append(r)
nets=closure['seed_net_ids']
assert len(nets)==52
(out/'protocol.json').write_text(json.dumps({'inputs_sha256':inputs,'selected_nets':nets,'alphas':[0,256],'selection_rule':'entire frozen endpoint closure','scope':'matched same-background full-graph search, baseline placement, same candidate-derived endpoint-net cohort; no native input','source_sha256':{p.name:sha(p) for p in (out/'source').glob('*.py')}},indent=2)+'\n')
prep=time.monotonic()-t;predictions={};reports=[];ref={r['connection_id']:r for r in background['connections']}
for alpha in (0,256):
 t=time.monotonic();prediction,report=recompute(g,after,background,nets,alpha=alpha);wall=time.monotonic()-t
 changed=[r['connection_id'] for r in prediction['connections'] if tuple(r['physical_edge_ids'])!=tuple(ref[r['connection_id']]['physical_edge_ids'])]
 (out/f'prediction_{alpha}.json').write_text(json.dumps(prediction)+'\n');predictions[alpha]=prediction
 row={'alpha':alpha,'wall_s':wall,'report':report,'changed_vs_background':len(changed),'scores':scores(g,after,prediction['node_occupancy'])};reports.append(row)
 (out/f'report_{alpha}.json').write_text(json.dumps(row,indent=2)+'\n');print(json.dumps({k:v for k,v in row.items() if k!='report'}),flush=True)
assert all(sha(p)==h for p,h in inputs.items())
zero={r['connection_id']:r for r in predictions[0]['connections']}
changed=[r['connection_id'] for r in predictions[256]['connections'] if tuple(r['physical_edge_ids'])!=tuple(zero[r['connection_id']]['physical_edge_ids'])]
receipt={'preparation_wall_s':prep,'reports':reports,'pressure_only_changed_connection_ids':changed,'background_scores':scores(g,after,background['node_occupancy']),'inputs_unchanged':True,'limitations':['one prior development candidate','single frozen batch, not negotiated congestion','alpha fixed uncalibrated','native quality and total pipeline benefit unproven']}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'pressure_only_changed_connections':len(changed)}),flush=True)
