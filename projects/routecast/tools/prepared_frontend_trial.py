"""Persistent pre-route maps vs archived fresh projections on seven layouts."""
import json,shutil,time
from pathlib import Path
from pre_route_endpoints import sha
from prepared_endpoints import PreparedEndpoints

out=Path('experiments/prepared_frontend_2026-10-04')
if out.exists():raise ValueError('fresh output required')
prior=Path('experiments/matched_hpwl_trial_2026-10-04');base=json.loads(Path('experiments/pre_route_endpoints_2026-10-04/diffeq_endpoints.json').read_text());inputs=base['inputs']
out.mkdir();(out/'source').mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
files={**inputs}
for cid in range(1,8):
    for kind,path in [('place',prior/f'candidate_{cid}.place'),('expected',prior/f'candidate_{cid}_endpoints.json')]:files[f'{kind}_{cid}']={'path':str(path.resolve()),'sha256':sha(path)}
protocol={'scope':'seven unchanged matched-HPWL placements, no native inputs','inputs':files,'static_identity_policy':'hash static net/graph before and after each query','source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.monotonic();prepared=PreparedEndpoints(inputs['net']['path'],inputs['graph']['path'],inputs['place']['path']);initialize=time.monotonic()-start;reports=[]
for cid in range(1,8):
    expected=json.loads(Path(files[f'expected_{cid}']['path']).read_text());start=time.monotonic();actual,_=prepared.project(files[f'place_{cid}']['path']);wall=time.monotonic()-start
    for field in ('connections','net_names','excluded_nets','clock_policy','graph_sha256','inputs'):
        assert actual[field]==expected[field],field
    target=out/f'projected_{cid}.json';target.write_text(json.dumps(actual,indent=2)+'\n');r={'candidate_id':cid,'connections':len(actual['connections']),'project_wall_s':wall,'fresh_endpoint_identity_and_inputs_match':True,'artifact_sha256':sha(target)};reports.append(r);print(json.dumps(r),flush=True)
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'initialize_wall_s':initialize,'total_project_wall_s':sum(r['project_wall_s'] for r in reports),'reports':reports,'scope':'frontend stage only; not end-to-end timing or optimization quality'},indent=2)+'\n')
