"""Real full12 parity plus controlled temporary read mutation rejection."""
import json,time,tempfile
from pathlib import Path
from unittest.mock import patch
from certified_budget_batch_gate_v1 import preflight_batch
from certified_budget_execution_gate_v2 import InvalidEvidence
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/certified_budget_batch_gate_v1_2026-10-08';D.mkdir(exist_ok=False);B=R/'experiments/branch_budget_admission_census_v1_2026-10-08'
cs=json.loads((B/'protocol.json').read_text())['cases'];cases=[dict(admission=str(B/f'w{c["width"]}_m{c["index"]}_admission.json'),endpoints=c['target'],budget=c['budget']) for c in cs]
start=time.perf_counter();result=preflight_batch(B/'verification.json',cases);seconds=time.perf_counter()-start
assert len(result['decisions'])==12
for c,x in zip(cs,result['decisions']):
 p=R/f'experiments/strict_budget_cohort_entry_v2_2026-10-08/w{c["width"]}_m{c["index"]}/protocol.json'
 old=json.loads(p.read_text())['preflight']
 for k in ('decision','run_candidate_pipeline','connections','blockers','bindings'):assert x[k]==old[k]
# A temporary synthetic fixture tests epoch handling only, not scientific authority.
with tempfile.TemporaryDirectory(prefix='routecast-batch-epoch-') as tmp:
 t=Path(tmp);ep=t/'ep.json';bp=t/'bp.json';ap=t/'a.json';vp=t/'v.json'
 ep.write_text(json.dumps({'connections':[{'connection_id':0}]}));bp.write_text(json.dumps({'budgets_ns':{},'default_budget_ns':'1'}))
 ap.write_text(json.dumps({'bindings':{str(ep):sha(ep),str(bp):sha(bp)},'rows':[{'connection_id':0,'minimum_seconds':'1/1000000000','budget_ns':'1','relaxed_path_budget_feasible':True}],'admitted':True}))
 vp.write_text(json.dumps({'all_twelve_cases_independent_admission_pass':True,'bindings':{str(ap):sha(ap)}}));fixture=[dict(admission=ap,endpoints=ep,budget=bp)]
 assert preflight_batch(vp,fixture)['decisions'][0]['run_candidate_pipeline']
 original=Path.read_text
 def mutate(path,*args,**kwargs):
  text=original(path,*args,**kwargs)
  if path==bp:bp.write_text(text+' ')
  return text
 with patch.object(Path,'read_text',mutate):
  try:preflight_batch(vp,fixture)
  except InvalidEvidence:pass
  else:raise AssertionError('Read mutation accepted')
 bp.write_text(json.dumps({'budgets_ns':{},'default_budget_ns':'1'}));assert preflight_batch(vp,fixture)['decisions'][0]['run_candidate_pipeline']
bindings=dict(result['bindings'])
for f in (Path(__file__),R/'tools/certified_budget_batch_gate_v1.py'):bindings[str(f)]=sha(f)
report=dict(bindings=bindings,decisions=result['decisions'],all12_exact_entry_decision_parity=True,controlled_mutation_rejected_and_recovered=True,synthetic_positive_only=True,batch_seconds=seconds,scope='Full12 same certified original-budget decisions/blockers/bindings as actual strict entries. Temporary synthetic positive/read mutation contract only. No native launch, fresh floor production or wholeworkflow speedup.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS full12 parity, mutation reject/recover; batch seconds',seconds)
