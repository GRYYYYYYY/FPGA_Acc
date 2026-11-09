"""Unfitted overflow>0 diagnostic versus authenticated native finite-budget outcomes."""
import json,sys
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
D=R/'experiments/sha1_width_models_v1_2026-10-10';bindings=closure([Path(__file__)])
def auth(p):
 d=json.loads(p.read_text());bindings[str(p)]=sha(p)
 for k,h in d['bindings'].items():assert sha(k)==h;bindings[k]=h
 return d
models=auth(D/'cohort_verification_v1.json');outcomes=auth(R/'experiments/sha1_native_abort_policy_v1_2026-10-10/outcome_verification_v1.json');physical=auth(R/'experiments/sha1_native_abort_policy_v1_2026-10-10/96/physical_verification_v1.json');assert physical['all_original_XML_physical_queries_branch_arcs_and_capacity_pass']
assert [x['width'] for x in models['rows']]==[x['width'] for x in outcomes['rows']]==[32,64,96];rows=[]
for m,o in zip(models['rows'],outcomes['rows']):
 status=o['status'];assert status in ['NATIVE_100_ITERATION_BUDGET_FAILURE','NATIVE_FULL_SUCCESS_PENDING_INDEPENDENT_ROUTE_AUDIT'];failure=status.startswith('NATIVE_100')
 rows.append(dict(width=m['width'],observed_native_100_budget_failure=failure,initial_overflow_units=m['initial_overflow_units'],final_overflow_units=m['final_overflow_units'],naive_initial_nonzero_overflow_predicts_failure=m['initial_overflow_units']>0,naive_final_nonzero_overflow_predicts_failure=m['final_overflow_units']>0))
metrics={}
for stage in ['initial','final']:
 counts=Counter((r[f'naive_{stage}_nonzero_overflow_predicts_failure'],r['observed_native_100_budget_failure']) for r in rows);tp,fp,fn,tn=[counts[x] for x in [(True,True),(True,False),(False,True),(False,False)]];assert (tp,fp,fn,tn)==(2,1,0,0)
 metrics[stage]=dict(tp=tp,fp=fp,fn=fn,tn=tn,precision=tp/(tp+fp),recall=tp/(tp+fn),specificity=tn/(tn+fp))
assert all(sha(k)==h for k,h in bindings.items())
(D/'failure_score_diagnostic_v1.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,metrics=metrics,threshold='strictly nonzero original-graph sketch overflow, no fitted threshold',scope='Three widths of same exposed SHA design, native outcomes known; diagnostic invalidates overflow>0 as sufficient failure certificate. Perfect ranking across these widths is confounded by width, not heldout predictive validity. No threshold training, claim of mathematical infeasibility, classifier efficacy or netgain.'),indent=2)+'\n');print('NONZERO_OVERFLOW_BASELINE',metrics)
