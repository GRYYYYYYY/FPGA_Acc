"""Compare authenticated complete trials; no paired replicate speedup claim."""
import json,math
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
versions=[('v9','2026-10-09','v6'),('v10','2026-10-09','v7')]
rows=[];bindings={str(Path(__file__)):sha(Path(__file__))};cases=[]
for version,date,stageversion in versions:
 d=R/f'experiments/ultraembedded_mmc_continuous_workflow_{version}_{date}'
 files=[d/'verification.json',d/f'stage_cost_verification_{stageversion}.json']
 v,s=[json.loads(p.read_text()) for p in files]
 assert v['all_cases_both_complete_arms_authenticated'] and s['stage_accounting_pass']
 for data in [v,s]:
  for p,h in data['bindings'].items():assert sha(p)==h,(p,h)
 bindings.update({str(p):sha(p) for p in files})
 assert len(v['cases'])==1 and v['cases'][0]['name']=='mmc'
 cases.append(v['cases'][0])
 costs={}
 for arm in s['rows']:
  assert arm['arm'] in ['cold','seed']
  costs[arm['arm']]={Path(x['log']).name if 'log' in x else x['stage']:x['seconds'] for x in arm['stages']}
 ct=v['cold_continuous_cohort_seconds'];st=v['seed_continuous_cohort_seconds']
 assert math.isclose(st/ct,v['seed_over_cold_ratio'])
 rows.append(dict(version=version,cold_seconds=ct,seed_seconds=st,seed_over_cold=st/ct,net_gain=st<ct,joint_time_and_printed_qor_gate=v['observed_single_trial_joint_time_and_printed_native_qor_gate'],stages=costs))
for arm in ['cold','seed']:
 a,b=[c['arms'][arm] for c in cases]
 assert a['required']==b['required'] and a['input_sha256']==b['input_sha256'] and a['rr_sha256']==b['rr_sha256']
 def normalized(cmd):
  cmd=cmd.copy();cmd[cmd.index('--read_rr_graph')+1]='MATCHED_RR';return cmd
 assert normalized(a['command'])==normalized(b['command'])
old,new=rows
audit_names=['mmc_initial_audit.log','mmc_sketch_audit.log','mmc_events_audit.log']
old_audits=sum(old['stages']['seed'][name] for name in audit_names)
new_audits=new['stages']['seed']['mmc_shared_audits.log']
out=dict(bindings=bindings,trials=rows,matched_frozen_inputs_and_rr_and_native_command=True,
 observed_three_audit_sum_seconds_difference=new_audits-old_audits,
 old_three_separate_audit_seconds=old_audits,new_combined_audit_seconds=new_audits,
 observed_cold_total_seconds_difference=new['cold_seconds']-old['cold_seconds'],
 observed_seed_total_seconds_difference=new['seed_seconds']-old['seed_seconds'],
 observed_seed_over_cold_ratio_difference=new['seed_over_cold']-old['seed_over_cold'],
 observed_model_and_seed_serialization_seconds_difference=new['stages']['seed']['mmc_model_native_seed.log']-old['stages']['seed']['mmc_model_native_seed.log'],
 scope='Two sequential historical single trials, not paired replicates or causal attribution. All complete validation costs included. Shared graph context alone does not establish complete net gain; both complete joint time/printed QoR gates retained. No strict-heldout, HDL, real async timing or silicon conclusion.')
shared_path=R/'experiments/ultraembedded_mmc_continuous_workflow_v10_2026-10-09/seed/model/mmc/shared_audit_receipt.json'
shared=json.loads(shared_path.read_text())
assert shared['all_three_complete_audits_pass'] and shared['complete_audit_bodies_AST_preserved'] and shared['fresh_independent_graph_context']
assert shared['diagnostics']['contexts']==shared['diagnostics']['context_loads']==1 and shared['diagnostics']['accesses']==3 and shared['diagnostics']['independent_xml_parses']==2
assert all(sha(p)==h for p,h in shared['bindings'].items())
bindings[str(shared_path)]=sha(shared_path)
old_model=R/'experiments/ultraembedded_mmc_continuous_workflow_v9_2026-10-09/seed/model/mmc'
new_model=R/'experiments/ultraembedded_mmc_continuous_workflow_v10_2026-10-09/seed/model/mmc'
for name in ['floors.json','initial.json','sketch.json','round0.json','round1.json']:
 a,b=old_model/name,new_model/name
 assert json.loads(a.read_text())==json.loads(b.read_text()),name
 bindings.update({str(a):sha(a),str(b):sha(b)})
rounds=[json.loads((p/'receipt.json').read_text())['rounds'] for p in [old_model,new_model]]
assert len(rounds[0])==len(rounds[1])==2
for a,b in zip(*rounds):
 assert {k:v for k,v in a.items() if k not in ['state_file','seconds']}=={k:v for k,v in b.items() if k not in ['state_file','seconds']}
old_native=old_model.parents[1]/'native/mmc';new_native=new_model.parents[1]/'native/mmc'
for name in ['subset.json','seed.route','bindings.json']:
 a,b=old_native/name,new_native/name
 assert a.read_bytes()==b.read_bytes(),name
 bindings.update({str(a):sha(a),str(b):sha(b)})
out['full_model_frames_events_and_native_seed_inputs_equal']=True
assert all(sha(p)==h for p,h in bindings.items())
d=R/'experiments/mmc_complete_workflow_v9_v10_comparison_v1_2026-10-09';d.mkdir(exist_ok=True)
(d/'comparison.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['bindings','trials']},indent=2))
