"""Authenticate all recorded MMC continuous workflow results before proposing repeats."""
import json,re
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
def main():
 rows=[];bindings={str(Path(__file__).resolve()):sha(Path(__file__))};cache={}
 def digest(path):
  path=str(path)
  if path not in cache:cache[path]=sha(path)
  return cache[path]
 for root in sorted((R/'experiments').iterdir()):
  if not root.is_dir() or 'mmc' not in root.name.lower() or 'workflow' not in root.name.lower():continue
  proof=root/'verification.json'
  if not proof.is_file() or proof.stat().st_size>8*2**20:continue
  v=json.loads(proof.read_text())
  if 'seed_over_cold_ratio' not in v:continue
  stagepaths=list(root.glob('stage_cost_verification_v*.json'))
  stage=max(stagepaths,key=lambda p:int(re.search(r'_v(\d+)\.json$',p.name)[1])) if stagepaths else None;s=json.loads(stage.read_text()) if stage else dict(bindings={},rows=[],stage_accounting_pass=False);bad=[]
  for p in [v,s]:
   for path,h in p['bindings'].items():
    try:actual=digest(path)
    except FileNotFoundError:actual=None
    if actual!=h:bad.append(dict(path=path,expected=h,actual=actual))
  bindings[str(proof)]=digest(proof)
  if stage:bindings[str(stage)]=digest(stage)
  cost={row['arm']:{Path(x['log']).name if 'log' in x else x['stage']:x['seconds'] for x in row['stages']} for row in s['rows']}
  rows.append(dict(root=root.name,all_cases_reported_authenticated=v['all_cases_both_complete_arms_authenticated'],stage_accounting_proof_present=stage is not None,stage_accounting_reported_pass=s['stage_accounting_pass'],current_binding_reauthentication_pass=not bad,binding_mismatches=bad,cold_seconds=v['cold_continuous_cohort_seconds'],seed_seconds=v['seed_continuous_cohort_seconds'],seed_over_cold=v['seed_over_cold_ratio'],recorded_net_time_gain=v['observed_single_trial_continuous_time_gain'],joint_time_printed_QoR_pass=v.get('observed_single_trial_joint_time_and_printed_native_qor_gate'),recorded_stage_seconds=cost))
 assert rows
 out=R/'experiments/authenticated_mmc_complete_workflow_inventory_v3_2026-10-17';out.mkdir()
 result=dict(inventory_complete=True,recorded_workflows=len(rows),current_bindings_pass_count=sum(x['current_binding_reauthentication_pass'] for x in rows),all_recorded_time_gates_negative=not any(x['recorded_net_time_gain'] for x in rows),rows=rows,bindings=bindings,scope='Existing single sequential historical workflow trials only. Different candidate semantics/timing dates cannot be pooled as paired repetitions or used to select a fastest conventional baseline. Reauthentication failures stay explicit. No new native run or label generation.',promoted=False)
 (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('recorded',len(rows),'current bindings pass',result['current_bindings_pass_count'],'time gains',sum(x['recorded_net_time_gain'] for x in rows))
 for x in rows:
  if x['binding_mismatches']:print('DRIFT',x['root'],x['binding_mismatches'][:3])
if __name__=='__main__':main()
