"""Authenticated nested component costs from the completed same-run ABBA."""
import json,statistics
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'paired_history_cost_decomposition_v1_2026-10-09';bindings={str(Path(__file__).resolve()):sha(Path(__file__))}
def read(p):
 d=json.loads(p.read_text());bindings[str(p)]=sha(p)
 for name,digest in d['bindings'].items():
  assert sha(name)==digest,name
  assert name not in bindings or bindings[name]==digest
  bindings[name]=digest
 return d
full=read(E/'paired_history_chain_v1_2026-10-09/verification.json');read(E/'paired_history_chain_v1_2026-10-09/independent_verification.json')
rows=[]
for arm in full['rows']:
 components=dict(history=0.,joint_selection=0.,proof_feedback=0.,serialization=0.,native=0.,canonical=0.,quality=0.);solver=0.
 for step in range(1,4):
  prefix=f"paired_history_chain_v1_arm{arm['arm']}_step{step}"
  if arm['mode']=='online':
   for index,key in enumerate(('history','joint_selection','proof_feedback','serialization')):
    r=read(E/f'{prefix}_stage_{index}_2026-10-09/verification.json');components[key]+=r['component_seconds'];solver+=r.get('solver_seconds',0.)
   n=read(E/f'{prefix}_stage_4_2026-10-09/receipt.json');c=read(E/f'{prefix}_stage_5_2026-10-09/receipt.json');q=read(E/f'{prefix}_stage_6_2026-10-09/verification.json')
  else:
   n=read(E/f'{prefix}_native_v1_2026-10-09/receipt.json');c=read(E/f'{prefix}_canonical_v1_2026-10-09/receipt.json');q=read(E/f'{prefix}_quality_v1_2026-10-09/verification.json')
  components['native']+=n['component_seconds'];components['canonical']+=c['component_seconds'];components['quality']+=q['verification_seconds']
 residual=arm['workflow_seconds']-sum(components.values());assert residual>=0
 rows.append(dict(arm=arm['arm'],mode=arm['mode'],workflow_seconds=arm['workflow_seconds'],components=components,solver_seconds_nested=solver,unattributed_seconds=residual))
means={}
for mode in ('online','cold'):
 group=[r for r in rows if r['mode']==mode]
 means[mode]=dict(workflow_seconds=statistics.mean(r['workflow_seconds'] for r in group),components={key:statistics.mean(r['components'][key] for r in group) for key in group[0]['components']},solver_seconds_nested=statistics.mean(r['solver_seconds_nested'] for r in group),unattributed_seconds=statistics.mean(r['unattributed_seconds'] for r in group))
optimistic=means['online']['workflow_seconds']-sum(means['online']['components'][key] for key in ('history','joint_selection','proof_feedback'))
report=dict(bindings=bindings,rows=rows,means=means,optimistic_free_candidate_production_seconds=optimistic,optimistic_to_cold_ratio=optimistic/means['cold']['workflow_seconds'],scope='Same-run retrospective nested components, solver included in joint/feedback and not added twice. Residual includes independent candidate/proof audits, setup, startup, binding/authentication, publication and uninstrumented costs. No per-stage attribution of residual or achievable speedup claim.')
D.mkdir(exist_ok=False);(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k not in ('bindings','rows')},flush=True)
