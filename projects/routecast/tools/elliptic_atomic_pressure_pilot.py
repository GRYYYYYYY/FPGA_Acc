"""One deterministic development net, full physical own-excluded pressure search."""
import json,shutil,time
from pathlib import Path
from pre_route_endpoints import sha
from prepared_endpoints import PreparedEndpoints
from rr_graph import read_rr_graph
from atomic_pressure_recompute import recompute
from feedback_scores import scores
out=Path('experiments/elliptic_atomic_pressure_pilot_2026-10-05')
if out.exists():raise ValueError('fresh output required')
out.mkdir();(out/'source').mkdir()
for f in Path('tools').glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
epath=Path('experiments/elliptic_endpoints_2026-10-04/endpoints.json');e=json.loads(epath.read_text());place=Path('experiments/elliptic_local_candidates_2026-10-05/candidate_6.place');pfile=Path('experiments/elliptic_prospective_feedback_2026-10-05/candidate_6_prediction.json');cfile=Path('experiments/elliptic_sketch_neighborhood_2026-10-05/closure_0.json')
inputs={str(p):sha(p) for p in (epath,place,pfile,cfile)};inputs.update({v['path']:v['sha256'] for v in e['inputs'].values()});assert all(sha(p)==h for p,h in inputs.items())
t=time.monotonic();g=read_rr_graph(e['inputs']['graph']['path']);frontend=PreparedEndpoints(e['inputs']['net']['path'],e['inputs']['graph']['path'],e['inputs']['place']['path']);after,_=frontend.project(place);background=json.loads(pfile.read_text());closure=json.loads(cfile.read_text());groups={}
for r in after['connections']:groups.setdefault(r['net_id'],[]).append(r)
net=min(closure['seed_net_ids'],key=lambda n:(len(groups[n]),n))
(out/'protocol.json').write_text(json.dumps({'inputs_sha256':inputs,'selected_net':net,'selection_rule':'min connection count then netID among frozen endpoint closure','alpha':256,'scope':'one development net contract pilot; no native input or outcome-based choice','source_sha256':{p.name:sha(p) for p in (out/'source').glob('*.py')}},indent=2)+'\n')
prep=time.monotonic()-t;t=time.monotonic();prediction,report=recompute(g,after,background,[net],alpha=256);wall=time.monotonic()-t
ref={r['connection_id']:r for r in background['connections']};changed=[r['connection_id'] for r in prediction['connections'] if tuple(r['physical_edge_ids'])!=tuple(ref[r['connection_id']]['physical_edge_ids'])]
assert all(sha(p)==h for p,h in inputs.items())
(out/'prediction.json').write_text(json.dumps(prediction)+'\n');receipt={'preparation_wall_s':prep,'pressure_recompute_wall_s':wall,'report':report,'changed_connection_ids':changed,'background_scores':scores(g,after,background['node_occupancy']),'pressure_scores':scores(g,after,prediction['node_occupancy']),'inputs_unchanged':True,'limitations':['single net pilot','alpha uncalibrated fixed development value','does not prove native quality, legality or net speedup']}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
