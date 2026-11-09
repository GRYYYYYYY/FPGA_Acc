"""Authenticate full workflows and isolate unchanged prediction state from cost."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
roots={'control':R/'experiments/ultraembedded_mmc_actual_old_linear_direct_lattice_workflow_v13_2026-10-10','undo':R/'experiments/ultraembedded_mmc_actual_old_linear_undo_workflow_v14_2026-10-10'}
bindings=closure([Path(__file__)]);rows={}
def auth(path):
 data=json.loads(path.read_text())
 for section in ['bindings','files']:
  for p,h in data.get(section,{}).items():assert sha(p)==h,(path,p);bindings[p]=h
 bindings[str(path)]=sha(path)
 return data
for mode,d in roots.items():
 v=auth(d/'verification.json');assert v['all_cases_both_complete_arms_authenticated']
 cost=auth(d/('stage_cost_verification_v10.json' if mode=='control' else 'stage_cost_verification_v11.json'));assert cost['stage_accounting_pass']
 events=auth(d/'seed/model/mmc/verification.json')
 assert events['complete_fallback_attempt_membership_actual_old_objective_and_budget_checks_pass']
 shared=auth(d/'seed/model/mmc/shared_audit_receipt.json')
 assert shared['all_three_complete_audits_pass'] and shared['complete_audit_bodies_AST_preserved'] and shared['fresh_independent_graph_context']
 h=auth(d/'seed/handoff/mmc/receipt.json');assert h['selected_connections']+h['pending_connections']==h['required_connections']==115572
 rows[mode]=dict(cold_seconds=v['cold_continuous_cohort_seconds'],seed_seconds=v['seed_continuous_cohort_seconds'],ratio=v['seed_over_cold_ratio'],observed_time_gain=v['observed_single_trial_continuous_time_gain'],joint_gate=v['observed_single_trial_joint_time_and_printed_native_qor_gate'],arms=v['cases'][0]['arms'],handoff={k:h[k] for k in ['required_connections','selected_connections','pending_connections']},event_counts={k:events[k] for k in ['completed','events','committed','retained','fallback_calls','fallback_accepted','fallback_retained','overflow_units']})
a,b=rows['control'],rows['undo']
assert a['handoff']==b['handoff'] and a['event_counts']==b['event_counts']
for mode in ['cold','seed']:
 assert a['arms'][mode]['rr_sha256']==b['arms'][mode]['rr_sha256']
 assert a['arms'][mode]['input_sha256']==b['arms'][mode]['input_sha256']
 def normalized(cmd):
  cmd=cmd.copy();cmd[cmd.index('--read_rr_graph')+1]='MATCHED_GRAPH';return cmd
 assert normalized(a['arms'][mode]['command'])==normalized(b['arms'][mode]['command'])
for name in ['initial.json','floors.json','round0.json','round1.json','sketch.json']:
 paths=[d/'seed/model/mmc'/name for d in roots.values()]
 hashes=[sha(p) for p in paths];assert hashes[0]==hashes[1],name
 bindings.update({str(p):h for p,h in zip(paths,hashes)})
subsets=[auth(d/'seed/native/mmc/subset.json') for d in roots.values()];assert subsets[0]==subsets[1]
receipts=[auth(d/'seed/model/mmc/receipt.json') for d in roots.values()]
assert len(receipts[0]['rounds'])==len(receipts[1]['rounds'])==2
for left,right in zip(receipts[0]['rounds'],receipts[1]['rounds']):
 assert {k:v for k,v in left.items() if k not in ['seconds','state_file']}=={k:v for k,v in right.items() if k not in ['seconds','state_file']}

assert all(sha(p)==h for p,h in bindings.items())
delta=dict(cold_seconds=b['cold_seconds']-a['cold_seconds'],seed_seconds=b['seed_seconds']-a['seed_seconds'],seed_wirelength=b['arms']['seed']['wirelength']-a['arms']['seed']['wirelength'],seed_iterations=b['arms']['seed']['iterations']-a['arms']['seed']['iterations'],seed_diagnostic_cpd_ns=b['arms']['seed']['diagnostic_cpd_ns']-a['arms']['seed']['diagnostic_cpd_ns'])
result=dict(bindings=bindings,complete_matched_inputs_commands_predictions_seed_selection_and_events_pass=True,rows=rows,descriptive_undo_minus_direct_lattice_control=delta,scope='Two historical complete fixed-placement workflows, source-certified full scientific and cost gates. Current undo-stack trial within-arm cold/seed comparison remains authoritative; historical deltas are descriptive, not randomized/stable or causal undo-stack performance estimates. Asynchronous CPD remains diagnostic/uncharacterized; no HDL, strict heldout or silicon gain. Negative time/QoR gates retained.')
(roots['undo']/'direct_lattice_control_comparison_v3.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='bindings'},indent=2))
