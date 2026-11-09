"""Exact realized update support versus fixed native drift; no new gate."""
import json,sys
from pathlib import Path
from fractions import Fraction
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from versioned_digest_cache_v1 import Cache

def main():
 d=R/'experiments/mmc_terminal_batch_quality_v1_2026-10-18';proof=d/'research_decision_v1.json';p=json.loads(proof.read_text())
 assert p['status']=='all108_terminal_batch_metric_vectors_independently_verified'
 bindings={**p['bindings'],str(proof):sha(proof),**closure([Path(__file__)])}
 out=R/'experiments/mmc_terminal_forecast_support_v1_2026-10-18';out.mkdir();rows=[];cache=Cache()
 with cache.installed():
  assert all(sha(path)==h for path,h in bindings.items())
  for case in ['case_01','case_02','case_03']:
   path=d/case/'vectors.json';assert bindings[str(path)]==sha(path);vectors=json.loads(path.read_text())
   for domain,key in [('concrete','channels'),('spatial','bins')]:
    data=vectors[key]
    support={i for i,v in enumerate(data) if v['predictions']['native_retained_terminal_batch']!=v['predictions']['native_retained_off']}
    for label in ['cold','partial_seed_default','partial_seed_firstpass_preserve']:
     total=Fraction(0);outside=Fraction(0);old_error=Fraction(0);new_error=Fraction(0);changed=0;overlap=0
     for i,v in enumerate(data):
      truth=v['labels'][label];pr=v['predictions'];cap=v['capacity']
      drift=abs(Fraction(truth-pr['previous_native'],cap));total+=drift
      if i not in support:outside+=drift
      if drift:changed+=1;overlap+=int(i in support)
      old_error+=abs(Fraction(truth-pr['native_retained_off'],cap))
      new_error+=abs(Fraction(truth-pr['native_retained_terminal_batch'],cap))
     rows.append(dict(case=case,domain=domain,label=label,domain_size=len(data),actual_update_support=len(support),native_drift_nonzero_resources=changed,native_drift_resources_in_support=overlap,native_drift_density_L1=str(total),native_drift_density_L1_outside_support=str(outside),native_drift_L1_outside_support_fraction=str(outside/total) if total else None,relative_to_retained_off_density_error_delta=str(new_error-old_error),outside_scope='Realized25path model update support only; not a bound on arbitrary predictors, other native policies, rank metrics or potential enlarged updates.'))
   print('SUPPORT DIAGNOSTIC',case,flush=True)
  assert all(sha(path)==h for path,h in bindings.items())
  with (out/'diagnosis.json').open('x') as stream:json.dump(dict(status='complete',bindings=bindings,rows=rows,scope='Retrospective support diagnostic after independently verified fixed forecast evaluation. Exact rational density L1, previous-native to current-native drift. No label-driven selection, new metric gate, native run or utility claim.'),stream,indent=2)

if __name__=='__main__':main()
