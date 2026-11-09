"""Apply fixed primary gate, report every ablation and complete timing scopes."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure

def main():
 E=R/'experiments';root=E/'mmc_source_context_ablation_v1_2026-10-18';quality=E/'mmc_source_context_quality_v1_2026-10-18';bindings=closure([Path(__file__)])
 def load(p):bindings[str(p)]=sha(p);return json.loads(p.read_text())
 def admit(p):
  d=load(p);assert all(sha(k)==h for k,h in d['bindings'].items());bindings.update(d['bindings']);return d
 spec=admit(E/'mmc_source_context_input_ablation_protocol_v1_2026-10-18/protocol.json');audit=admit(root/'independent_audits/verification.json');assert audit['all9_full_frames_and_source_context_event_replays_pass'];q=admit(quality/'results.json');models=admit(root/'results.json');clock=admit(root/'producer_wall_clock_observation_v1.json');assert clock['status']=='original_producer_terminal_observed' and clock['complete_results_sha256']==sha(root/'results.json');arms=list(spec['arms']);assert spec['primary_candidate']==q['primary_candidate']=='source_history_and_post_STA';rows=[];gates={arm:[] for arm in arms}
 for case in ['case_01','case_02','case_03']:
  p=load(quality/case/'protocol.json');r=admit(quality/case/'comparison.json');v=admit(quality/case/'verification.json');assert p['primary_candidate']=='source_history_and_post_STA' and p['primary_controls']==['raw_min_on','previous_native'];assert v['status']=='pass' and v['histogram_rank_topk_mae_checks']==v['truth_tie_interval_checks']==16 and v['primary_gate_pass']==r['primary_gate_pass'];armchecks={}
  for arm in arms:
   checks=[]
   for control in ['raw_min_on','previous_native']:
    cs=[]
    for scope in ['concrete','spatial']:
     for metric in ['spearman','precision_at_k']:
      reference=r['metrics']['cold'][control][scope][metric];value=r['metrics']['cold'][arm][scope][metric];eps=1e-12 if metric=='spearman' else 0;cs.append(dict(scope=scope,metric=metric,reference=reference,candidate=value,nonregression=reference is not None and value is not None and value>=reference-eps,strict_improvement=reference is not None and value is not None and value>reference+eps))
    checks.append(dict(control=control,pass_primary_gate=all(c['nonregression'] for c in cs) and any(c['strict_improvement'] for c in cs),comparisons=cs))
   passed=all(c['pass_primary_gate'] for c in checks);gates[arm].append(passed);armchecks[arm]=dict(pass_original_case_gate=passed,checks=checks)
  assert armchecks['source_history_and_post_STA']['pass_original_case_gate']==r['primary_gate_pass'];rows.append(dict(case=case,arms=armchecks,metrics=r['metrics']['cold']))
 primary=all(gates['source_history_and_post_STA']);assert primary==q['all3_original_cold_primary_gate_pass'];staging=admit(E/'mmc_source_context_inputs_v1_2026-10-18/receipt.json');capture=admit(E/'mmc_dense_post_STA_source_v1_2026-10-18/receipt.json');build=admit(R/'build/dense_post_STA_source_v1_2026-10-18/receipt.json');assert all(sha(k)==h for k,h in bindings.items())
 result=dict(status='registered_source_context_primary_original_cold_gate_pass_native_utility_unproven' if primary else 'registered_source_context_primary_original_cold_gate_failed_no_native_promotion',bindings=bindings,registered_primary='source_history_and_post_STA',all3_primary_original_cold_gate_pass=primary,ablation_original_cohort_gates={arm:all(values) for arm,values in gates.items()},cases=rows,observed_model_runs=models['cases'],whole9model_producer_wall_seconds_interval=[clock['elapsed_wall_seconds_lower_bound'],clock['elapsed_wall_seconds_upper_bound']],shared_graph_setup_seconds=models['shared_graph_setup_seconds'],source_acquisition_costs=dict(compile_seconds=build['compile_seconds'],link_seconds=build['link_seconds'],capture_native_seconds=capture['native_capture_process_seconds'],input_staging_seconds=staging['staging_process_seconds']),timing_scope='Whole9arm-case producer and shared graph; upstream acquisition/staging recorded separately, no cache amortization or matched full-control claim. Return timers include receipt/end-of-call work; internal receipt samples do not. Factorial total includes secondary arms, not the cost of primary alone.',no_posthoc_primary_selection=True,native_utility_trial_executed=False,accepted_matched_complete_workflow_gain=False,original_source_zero_counter_gate=False,scope='All3 exposed development layouts. Native source timing prior only, not fresh target STA or native-equivalent price policy. All original cold domains/K/ties/controls/guards remain. Secondary ablation success cannot substitute for registered primary. Strict unseen family, varied native failures, accepted complete-flow gain and hardware remain unmet.')
 with (root/'research_decision_v1.json').open('x') as f:json.dump(result,f,indent=2)
 print(result['status'],flush=True)
if __name__=='__main__':main()
