"""Reuse unchanged tested stage lifecycle; verify new admission on actual complete inputs."""
import ast,copy,json
from pathlib import Path
import neuron_proxy_budget_trial_v2 as trial
import neuron_continue_primary_trial_v1 as prior
from audit_proxy_budget_initial_parity_v1 import audit,protocol
R=trial.R

def function(path,name):
 return next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name==name)
def main():
 out=R/'experiments/neuron_proxy_budget_trial_guard_v2_2026-10-17';out.mkdir()
 sources=[Path(trial.__file__),Path(prior.__file__)]
 for name in ['run_stage','run']:
  assert ast.dump(function(sources[0],name))==ast.dump(function(sources[1],name))
 a=ast.dump(function(sources[0],'metrics'));b=ast.dump(function(sources[1],'metrics'))
 # Only method labels and archived metric dictionary key differ.
 a=a.replace("value='budget1'","value='CANDIDATE'").replace("value='continued1'","value='CONTROL'")
 b=b.replace("value='continued1'","value='CANDIDATE'").replace("value='retained1'","value='CONTROL'").replace("value='candidate1'","value='CONTROL'")
 assert a==b
 oldproof=trial.load(R/'experiments/neuron_continue_primary_trial_guard_v1_2026-10-17/verification.json');assert oldproof['all_pass'];trial.check(oldproof['bindings'])
 baseline=trial.baseline_gate()
 fixture=R/'experiments/xtea_proxy_budget_audit_fixture_v1_2026-10-17';control=R/'experiments/xtea_scaled_present_factor1_pipeline_v1_2026-10-15/model'
 c=trial.load(fixture/'model/initial.json');b=trial.load(control/'initial.json');pins=trial.load(R/'experiments/xtea_retained_native_inputs_v1_2026-10-13/criticality/initial_connection_criticalities.json')
 assert audit(c,b,pins)['connections']==2450
 protocol(trial.load(fixture/'model/protocol.json'),trial.load(R/'experiments/xtea_continue_primary_audit_fixture_v1_2026-10-17/model/protocol.json'))
 cases=0
 for kind in ['budget','floor','path','ledger','duplicate','criticality','pin']:
  bad=copy.deepcopy(c);badpins=copy.deepcopy(pins)
  if kind=='budget':bad['records'][0]['budget_integer']+=1
  elif kind=='floor':bad['records'][0]['floor_integer']+=1
  elif kind=='path':bad['records'][0]['answer']['physical_edge_ids']=[]
  elif kind=='ledger':bad['ledger'][next(iter(bad['ledger']))]+=1
  elif kind=='duplicate':bad['records'][1]=copy.deepcopy(bad['records'][0])
  elif kind=='criticality':badpins[0]['criticality_float32_text']='1'
  elif kind=='pin':badpins[1]['local_sink_pin']=badpins[0]['local_sink_pin'];badpins[1]['net']=badpins[0]['net']
  try:audit(bad,b,badpins)
  except (AssertionError,KeyError):cases+=1
  else:raise AssertionError('Corruption accepted '+kind)
 for key in ['present_factor','budget_policy','primary_completion_policy']:
  cp=copy.deepcopy(trial.load(fixture/'model/protocol.json'));cp[key]='corrupt'
  try:protocol(cp,trial.load(R/'experiments/xtea_continue_primary_audit_fixture_v1_2026-10-17/model/protocol.json'))
  except AssertionError:cases+=1
  else:raise AssertionError(key)
 initial=trial.load(trial.BASELINE/'model/initial.json');candidate=copy.deepcopy(initial)
 budgets={x['connection_id']:x for x in map(json.loads,(trial.PREREG/'candidate_budgets.jsonl').read_text().splitlines())}
 for row in candidate['records']:row['budget_integer']=budgets[row['connection_id']]['new_budget_integer']
 parity=audit(candidate,initial,trial.load(trial.CRITICALITY/'initial_connection_criticalities.json'));assert parity['connections']==77106 and parity['changed_budgets']==70437
 paths=[*sources,Path(__file__).resolve(),R/'tools/audit_proxy_budget_initial_parity_v1.py',R/'experiments/neuron_continue_primary_trial_guard_v1_2026-10-17/verification.json',fixture/'closed_admission_v1.json',trial.PREREG/'candidate_budgets.jsonl']
 bindings={str(p):trial.sha(p) for p in paths};bindings.update(baseline)
 trial.write(out/'verification.json',dict(all_pass=True,run_stage_and_run_AST_identical=True,all8_metrics_core_AST_identical_except_method_labels=True,existing_real_timeout_kernel_cap_kill_no_retry_evidence_reused=True,actual_XTEA_initial_and_protocol_accepted=True,complete_neuron_initial_budget_manifest_accepted=parity,admission_corruptions_refused=cases,bindings=bindings,new_neuron_model_submitted=False))
 print('PASS proxy-budget trial lifecycle and admission guards',cases,parity,flush=True)
if __name__=='__main__':main()
