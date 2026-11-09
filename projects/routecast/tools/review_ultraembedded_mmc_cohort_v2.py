"""Versioned MMC cohort review including retained failed and complete costs."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
old=R/'experiments/ultraembedded_mmc_cohort_review_v1_2026-10-08/review.json'
cost=R/'experiments/ultraembedded_mmc_continuous_workflow_v2_2026-10-08/verification.json'
failure=R/'experiments/ultraembedded_mmc_continuous_failure_review_v1_2026-10-08/review.json'
def load(p):return json.loads(p.read_text())
def auth(obj):
 if isinstance(obj,dict):
  for k,v in obj.items():
   if k in ('bindings','files') and isinstance(v,dict):
    for path,digest in v.items():assert sha(path)==digest,path
   else:auth(v)
 elif isinstance(obj,list):
  for x in obj:auth(x)
a=load(old);c=load(cost);f=load(failure)
for obj in (a,c,f):auth(obj)
for path in a['bindings']:
 if Path(path).suffix=='.json':auth(load(Path(path)))
assert c['all_cases_both_complete_arms_authenticated'] and not c['observed_single_trial_continuous_time_gain']
assert c['seed_continuous_cohort_seconds']>c['cold_continuous_cohort_seconds']
result=dict(a)
result['bindings']={**a['bindings'],**{str(p):sha(p) for p in (old,cost,failure,Path(__file__))}}
result['continuous_cost_v2']={k:c[k] for k in ('cold_continuous_cohort_seconds','seed_continuous_cohort_seconds','seed_over_cold_ratio','observed_single_trial_continuous_time_gain','scope')}
result['earlier_continuous_v1_failure']=dict(review=str(failure),retained=True,successful_full_cost=False,scope='Earlier event-audit timeout remains failed; no posthoc audit time splice or replacement.')
result['conclusions']=a['conclusions']+['Fresh complete validation-inclusive MMC seed/cold ratio2.8689091372395255; no observed whole workflow time gain in this single ordered trial.']
result['pending']=[x for x in a['pending'] if not x.startswith('Fresh continuous')]
result['scope']=a['scope']+' New review authenticates completed v2 full cost and retained v1 failure; candidate pin-index work is separate and not retroactively applied.'
assert all(sha(k)==v for k,v in result['bindings'].items())
out=R/'experiments/ultraembedded_mmc_cohort_review_v2_2026-10-08';out.mkdir();(out/'review.json').write_text(json.dumps(result,indent=2)+'\n');print('MMC cohort v2 authenticated; full cost negative; research requirements remain open')
