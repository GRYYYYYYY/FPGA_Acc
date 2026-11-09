"""Frozen all-candidate development ablation with common net cohort."""
import json,time,shutil
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from prepared_endpoints import PreparedEndpoints
from affected_connections import affected
from atomic_pressure_recompute import recompute
from feedback_scores import scores
out=Path('experiments/frisc_pressure_candidate_matrix_2026-10-05')
if out.exists():raise ValueError('fresh output required')
completed_background=json.loads(Path('experiments/frisc_topology_backgrounds_2026-10-05/receipt.json').read_text());assert len(completed_background['rows'])==9 and completed_background['inputs_unchanged']
start=time.monotonic();out.mkdir();(out/'source').mkdir()
for f in Path('tools').glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
epath=Path('experiments/frisc_endpoints_2026-10-05/endpoints.json');e=json.loads(epath.read_text());parent=Path('experiments/frisc_local_candidates_2026-10-05');old=Path('experiments/frisc_topology_backgrounds_2026-10-05')
places={0:Path(e['inputs']['place']['path']),**{cid:parent/f'candidate_{cid}.place' for cid in range(1,9)}}
backgrounds={0:Path('experiments/frisc_topology_backgrounds_2026-10-05/baseline_prediction.json'),**{cid:old/f'candidate_{cid}_prediction.json' for cid in range(1,9)}}
inputs={str(p):sha(p) for p in [epath,*places.values(),*backgrounds.values()]};inputs.update({v['path']:v['sha256'] for v in e['inputs'].values()});assert all(sha(p)==h for p,h in inputs.items())
g=read_rr_graph(e['inputs']['graph']['path']);frontend=PreparedEndpoints(e['inputs']['net']['path'],e['inputs']['graph']['path'],e['inputs']['place']['path']);endpoints={0:e};nets=set()
for cid in range(1,9):
 endpoints[cid],_=frontend.project(places[cid]);nets.update(affected(e,endpoints[cid])['affected_net_ids'])
# Preserve complete SOURCE groups across all placements for the common cohort.
while True:
 sources={r['source'] for ep in endpoints.values() for r in ep['connections'] if r['net_id'] in nets}
 expanded=nets|{r['net_id'] for ep in endpoints.values() for r in ep['connections'] if r['source'] in sources}
 if expanded==nets:break
 nets=expanded
protocol={'prospective_protocol_sha256':sha('experiments/frisc_prospective_protocol_2026-10-05/protocol.json'),'inputs_sha256':inputs,'common_net_ids':sorted(nets),'alphas':[0,256],'candidates':list(range(9)),'selection_rule':'min channel span, then overuse, then candidateID including baseline; diagnostic ranking only, existing timing-guarded policy not replaced','scope':'prospective additional frisc design; frozen method, same architecture, not family holdout, no native labels','source_sha256':{p.name:sha(p) for p in (out/'source').glob('*.py')}}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');prep=time.monotonic()-start
print(json.dumps({'common_nets':len(nets),'preparation_wall_s':prep}),flush=True);reports=[]
for cid in range(9):
 bg=json.loads(backgrounds[cid].read_text())
 for alpha in (0,256):
  t=time.monotonic();prediction,report=recompute(g,endpoints[cid],bg,nets,alpha=alpha);wall=time.monotonic()-t
  (out/f'prediction_{cid}_{alpha}.json').write_text(json.dumps(prediction)+'\n')
  row={'candidate_id':cid,'alpha':alpha,'wall_s':wall,'scores':scores(g,endpoints[cid],prediction['node_occupancy']),'report':report};reports.append(row)
  (out/f'report_{cid}_{alpha}.json').write_text(json.dumps(row,indent=2)+'\n');print(json.dumps({k:v for k,v in row.items() if k!='report'}),flush=True)
assert all(sha(p)==h for p,h in inputs.items())
ranking={str(alpha):[r['candidate_id'] for r in sorted((r for r in reports if r['alpha']==alpha),key=lambda r:(r['scores']['channel_net_span_sum'],r['scores']['predicted_channel_overuse_units'],r['candidate_id']))] for alpha in (0,256)}
(out/'receipt.json').write_text(json.dumps({'preparation_wall_s':prep,'full_wall_s':time.monotonic()-start,'ranking':ranking,'reports':reports,'input_hashes_unchanged':True,'limitations':['development labels already explored, not unseen-family','single frozen batch, not legal negotiated routing','prediction-only ranking; timing guard not evaluated','all arms sequential; no speed comparison claim']},indent=2)+'\n');print(json.dumps({'ranking':ranking}),flush=True)
