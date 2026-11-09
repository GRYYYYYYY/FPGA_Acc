"""Frozen unchanged two-round predictor on additional elliptic design."""
import json,shutil,time
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from connectivity_trial import construct
from hybrid_repair import repair
from lazy_region_search import LazyRegionalSearch
from physical_prediction_audit import audit
out=Path('experiments/elliptic_transfer_2026-10-04')
if out.exists():raise ValueError('fresh output required')
paths={'graph':Path('work/elliptic_graph_capture_2026-10-04/rr_graph.xml'),'endpoints':Path('experiments/elliptic_endpoints_2026-10-04/endpoints.json')}
out.mkdir();(out/'source').mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
p={'scope':'additional design transfer, no parameter retuning; same architecture; no heldout family claim','inputs':{k:{'path':str(v.resolve()),'sha256':sha(v)} for k,v in paths.items()},'refinement_rounds':2,'repair_margin':1,'budget':'all graph nodes','cost':'rr_length_switch','label_policy':'no native route/timing inputs','source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}}
(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');start=time.monotonic();g=read_rr_graph(paths['graph']);ep=json.loads(paths['endpoints'].read_text());load=time.monotonic()-start
start=time.monotonic();candidate=construct(g,ep,2);build=time.monotonic()-start
(out/'candidate.json').write_text(json.dumps(candidate)+'\n');print(json.dumps({'stage':'candidate','nodes':candidate['nodes'],'lifted':candidate['lifted_connections'],'wall_s':build}),flush=True)
start=time.monotonic();prediction=repair(g,ep,candidate,1,search_type=LazyRegionalSearch);repair_s=time.monotonic()-start
(out/'prediction.json').write_text(json.dumps(prediction)+'\n');checked=audit(g,ep,prediction,candidate)
r={'protocol_sha256':sha(out/'protocol.json'),'load_wall_s':load,'construct_wall_s':build,'repair_wall_s':repair_s,'completed':prediction['completed'],'requested':prediction['requested'],'methods':prediction['methods'],'candidate_work':candidate['work'],'repair_work':prediction['repair_work'],'independent_audit':checked,'artifacts':{f.name:sha(f) for f in out.glob('*.json') if f.name!='receipt.json'}}
assert all(sha(v['path'])==v['sha256'] for v in p['inputs'].values());(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
