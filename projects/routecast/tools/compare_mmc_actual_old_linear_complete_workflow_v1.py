"""Authenticated descriptive comparison of complete fixed-placement workflows.
Historical default arm timings are observations, not a randomized intervention.
"""
import json, sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
new=R/'experiments/ultraembedded_mmc_actual_old_linear_fallback_workflow_v11_2026-10-09'
old=R/'experiments/ultraembedded_mmc_continuous_workflow_v10_2026-10-09'
bindings={str(Path(__file__)):sha(Path(__file__))}
def load(path):
 data=json.loads(path.read_text())
 for section in ['bindings','files']:
  for p,h in data.get(section,{}).items():
   assert sha(p)==h,(path,p)
   bindings[p]=h
 bindings[str(path)]=sha(path)
 return data
rows={}
for name,d in [('default',old),('linear_actual_old',new)]:
 v=load(d/'verification.json')
 assert v['all_cases_both_complete_arms_authenticated']
 assert len(v['cases'])==1 and v['cases'][0]['name']=='mmc'
 cost=load(d/('stage_cost_verification_v7.json' if name=='default' else 'stage_cost_verification_v8.json'))
 assert cost['stage_accounting_pass']
 event=load(d/'seed/model/mmc/verification.json')
 assert event['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass']
 model=load(d/'seed/model/mmc/receipt.json')
 events=[e for r in model['rounds'] for e in r['events']]
 assert event['events']==len(events)
 for field,status in [('committed','COMMITTED'),('retained','RETAIN_BUDGET_OR_UNREACHABLE')]:
  assert event[field]==sum(e['status']==status for e in events)
 handoff=load(d/'seed/handoff/mmc/receipt.json')
 assert handoff['selected_connections']+handoff['pending_connections']==handoff['required_connections']==115572
 if name=='linear_actual_old':
  assert event['complete_fallback_attempt_membership_actual_old_objective_and_budget_checks_pass']
  fallback=[e for e in events if 'fallback' in e]
  assert event['fallback_calls']==len(fallback)
  assert event['fallback_accepted']==sum(e['fallback']['status']=='ACCEPT_STRICT_IMPROVEMENT' for e in fallback)
  assert event['fallback_retained']==len(fallback)-event['fallback_accepted']
 rows[name]=dict(arms=v['cases'][0]['arms'],cold_seconds=v['cold_continuous_cohort_seconds'],seed_seconds=v['seed_continuous_cohort_seconds'],seed_over_cold=v['seed_over_cold_ratio'],observed_time_gain=v['observed_single_trial_continuous_time_gain'],printed_native_qor_nonregression=v['matched_printed_native_qor_nonregression_gate'],joint_gate=v['observed_single_trial_joint_time_and_printed_native_qor_gate'],model_events={k:event[k] for k in ['events','committed','retained','completed','overflow_units']},fallback={k:event[k] for k in ['fallback_calls','fallback_accepted','fallback_retained'] if k in event},selected_connections=handoff['selected_connections'],pending_connections=handoff['pending_connections'])
a,b=rows['default'],rows['linear_actual_old']
for mode in ['cold','seed']:
 assert a['arms'][mode]['rr_sha256']==b['arms'][mode]['rr_sha256']
 assert a['arms'][mode]['input_sha256']==b['arms'][mode]['input_sha256']
 def normalize(cmd):
  c=cmd.copy();c[c.index('--read_rr_graph')+1]='MATCHED_GRAPH';return c
 assert normalize(a['arms'][mode]['command'])==normalize(b['arms'][mode]['command'])
delta=dict(seed_seconds=b['seed_seconds']-a['seed_seconds'],cold_seconds=b['cold_seconds']-a['cold_seconds'],seed_wirelength=b['arms']['seed']['wirelength']-a['arms']['seed']['wirelength'],seed_diagnostic_cpd_ns=b['arms']['seed']['diagnostic_cpd_ns']-a['arms']['seed']['diagnostic_cpd_ns'],seed_iterations=b['arms']['seed']['iterations']-a['arms']['seed']['iterations'])
assert all(sha(p)==h for p,h in bindings.items())
result=dict(bindings=bindings,complete_matched_inputs_commands_and_fallback_event_counts_pass=True,rows=rows,descriptive_candidate_minus_default=delta,scope='Complete fresh fixed-placement workflow observations. Each within-trial cold/seed comparison includes all producer-defined stages and unassigned overhead. Across historical trials differences are descriptive, not stable or causal fallback cost/quality estimates. Printed asynchronous CPD is uncharacterized diagnostic only; no HDL, strict heldout or silicon claim. Does not assert any time or quality gate passes.')
(new/'default_comparison_v1.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='bindings'},indent=2))
