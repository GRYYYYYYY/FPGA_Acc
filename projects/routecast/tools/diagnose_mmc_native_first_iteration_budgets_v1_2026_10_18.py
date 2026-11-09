"""All fixed-case budget failures and warm/prefix delays, without target labels."""
import json,hashlib
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()
def main():
 root=R/'experiments/mmc_native_first_iteration_v1_2026-10-18';pp=root/'physical_and_budget_verification_v1.json';physical=json.loads(pp.read_text());bindings={str(pp):sha(pp),str(Path(__file__).resolve()):sha(Path(__file__).resolve())};rows=[]
 for case in ['case_01','case_02','case_03']:
  warm=R/f'experiments/mmc_multiplacement_models_v1_2026-10-18/{case}/native_retained';wp=warm/'verification.json';w=json.loads(wp.read_text());dirty=set(w['dirty_nets']);sp=root/case/'diagnostic_sketch_v1.json';vp=root/case/'budget_violations_v1.json';v=json.loads(vp.read_text());old={x['connection_id']:x for x in json.loads((warm/'initial.json').read_text())['records']};new=json.loads(sp.read_text())['records'];assert len(new)==len(old)==115572;categories=Counter();changes=Counter();excess=Counter();failednets=set()
  for x in new:
   cid=x['connection_id'];a=old[cid];assert x['budget_integer']==a['budget_integer'];assert x['net_id']==a['net_id'];domain='endpoint_closure' if x['net_id'] in dirty else 'outside_endpoint_closure';delay=x['answer']['delay'];prior=a['answer']['delay'];changes[domain+('/shorter' if delay<prior else '/equal' if delay==prior else '/longer')]+=1
   if delay>x['budget_integer']:categories[domain]+=1;excess[domain]+=delay-x['budget_integer'];failednets.add(x['net_id'])
  assert sum(categories.values())==len(v)==next(x['budget_violations'] for x in physical['cases'] if x['case']==case)
  rows.append(dict(case=case,budget_violations_by_scope=dict(categories),budget_excess_integer_sum_by_scope=dict(excess),prefix_vs_warm_additive_delay_counts=dict(changes),NETs_with_at_least_one_budget_violation=len(failednets),NETs_with_all_pin_budgets_pass=55300-len(failednets),violating_NETs_outside_endpoint_closure=len(failednets-dirty)))
  for p in [wp,warm/'initial.json',sp,vp]:bindings[str(p)]=sha(p)
 result=dict(status='all3_prefix_budget_failure_scope_and_delay_comparison_complete',bindings=bindings,cases=rows,scope='Descriptive comparison with the audited warm initial state, not target final routes. Endpoint closure is a grouping, not a causal attribution. WholeNET budget pass does not imply low occupancy, native FULL, legal route or forecast utility. No candidate filtering or budget relaxation.')
 (root/'budget_scope_diagnostic_v1.json').open('x').write(json.dumps(result,indent=2)+'\n');print(json.dumps(rows,indent=2),flush=True)
if __name__=='__main__':main()
