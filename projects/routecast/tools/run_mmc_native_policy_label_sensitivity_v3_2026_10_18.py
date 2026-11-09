"""Supplemental both-policy label diagnostic on immutable existing forecasts."""
import json,sys,subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
D=R/'experiments/mmc_native_policy_label_sensitivity_v3_2026-10-18';P=R/'tools/evaluate_mmc_native_policy_label_sensitivity_v1_2026_10_18.py';V=R/'tools/verify_mmc_native_policy_label_sensitivity_v1_2026_10_18.py';proof=R/'experiments/mmc_partial_firstpass_recovery_v3_2026-10-18/independent_wire_work_comparison_v1.json';pv=json.loads(proof.read_text());assert pv['status']=='pass' and pv['all6_independent_wire_and_every_iteration_integer_fields_equal'];assert all(sha(p)==h for p,h in pv['bindings'].items());bindings={**pv['bindings'],str(proof):sha(proof),**closure([Path(__file__),P,V])}
(D/'logs').mkdir()
def run(case):
 if case=='case_02':
  p=D/case/'verification.json';v=json.loads(p.read_text());assert v['status']=='pass' and v['histogram_rank_topk_mae_checks']==20 and all(sha(q)==h for q,h in v['bindings'].items());print('REUSE CASE02 VERIFIED20VECTORS',flush=True);return dict(case=case,exit_code=0,reused_verified_case=True)
 print('POLICY LABEL MATRIX START',case,flush=True)
 for index,script in enumerate([P,V]):
  with (D/'logs'/(case+'_'+str(index)+'.log')).open('x') as f:code=subprocess.call([sys.executable,str(script),str(D/case)],cwd=R,stdout=f,stderr=subprocess.STDOUT)
  if code:return dict(case=case,stage=index,exit_code=code)
 return dict(case=case,exit_code=0)
rows=[]
with ThreadPoolExecutor(max_workers=3) as pool:
 for f in as_completed([pool.submit(run,c) for c in ['case_01','case_03']]):
  r=f.result();rows.append(r);print('POLICY LABEL MATRIX TERMINAL',r,flush=True)
  (D/'stages.json').write_text(json.dumps(rows,indent=2))
rows.append(run('case_02'))
assert all(r['exit_code']==0 for r in rows)
metrics=[]
for case in ['case_01','case_02','case_03']:
 p=D/case/'verification.json';v=json.loads(p.read_text());assert v['status']=='pass' and v['histogram_rank_topk_mae_checks']==20;bindings.update(v['bindings']);bindings[str(p)]=sha(p);r=json.loads((D/case/'comparison.json').read_text());metrics.append(dict(case=case,metrics=r['metrics'],fixed_original_metric_rule_comparisons=r['primary_checks']))
old=R/'experiments/mmc_multiplacement_quality_v1_2026-10-18/cohort_research_decision_v1.json';bindings[str(old)]=sha(old);assert all(sha(p)==h for p,h in bindings.items())
with (D/'supplemental_decision_v1.json').open('x') as f:json.dump(dict(status='retrospective_policy_label_sensitivity_verified',bindings=bindings,rows=metrics,all60_full_domain_metric_vectors_independently_verified=True,original_cold_label_decision=str(old),original_cold_label_decision_unchanged=True,scope='Both fixed routing policies and all3exposed placements; existing predictions unchanged. Metric-rule outcomes here are retrospective sensitivity diagnostics, not replacement promotion gates. No unseen-family, end-to-end timing or hardware claim.'),f,indent=2)
print('ALL60POLICY LABEL METRIC VECTORS VERIFIED',flush=True)
