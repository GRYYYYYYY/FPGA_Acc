"""Evidence-bound interim research review; no new search, fitting or gate changes."""
import json,datetime
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/joint_capacity_direction_review_v1_2026-10-21';D.mkdir(exist_ok=True)
paths={
 'binary_diagnosis':R/'experiments/joint_capacity_direction_review_v1_2026-10-21/binary_metric_diagnosis_v1.json',
 'capacity':R/'experiments/mmc_expanded40_joint_CBS_v1_2026-10-21/case01_full_candidate_verification_v1.json',
 'closure':R/'experiments/mmc_expanded41_conflict_first_CBS_v1_2026-10-21/independent_branch_closure_v1.json',
 'quality':R/'experiments/mmc_case01_legal_candidate_quality_v1_2026-10-21/results.json',
 'joint_run':R/'experiments/mmc_expanded41_conflict_first_CBS_v1_2026-10-21/verification.json',
 'joint_decision':R/'experiments/mmc_expanded41_conflict_first_CBS_v1_2026-10-21/research_decision_v1.json',
 'bank_producer':R/'experiments/mmc_all_NET_feedback_v1_2026-10-18/results.json',
 'bank_cost':R/'experiments/mmc_all_NET_feedback_v1_2026-10-18/cost_boundary_audit_v1.json',
 'bank_plan':R/'experiments/mmc_complete_NET_candidate_choice_diagnostic_protocol_v1_2026-10-19/protocol.json',
 'bank_membership':R/'experiments/mmc_candidate_ownership_implications_v1_2026-10-19/review.json',
 'wider_context':R/'experiments/mmc_prior_wider_context_failure_scope_audit_v1_2026-10-19/audit.json',
 'state_mechanisms':R/'experiments/mmc_state_dependent_mechanism_scope_audit_v1_2026-10-19/audit.json',
 'ridge':R/'experiments/mmc_coupled_ridge_development_v1_2026-10-19/research_decision_v1.json',
 'count_chooser':R/'experiments/mmc_input_only_closed_choice_v1_2026-10-19/research_decision_v1.json',
 'frequency':R/'experiments/mmc_owner_frequency_development_v1_2026-10-19/research_decision_v1.json',
 'signature':R/'experiments/mmc_owner_signature_ambiguity_v1_2026-10-19/research_decision_v1.json',
 'DAG_support':R/'experiments/mmc_missing_owner_DAG_diagnosis_v1_2026-10-19/research_decision_v1.json'}
docs={k:json.loads(p.read_text()) for k,p in paths.items()};bindings={str(p):sha(p) for p in [*paths.values(),Path(__file__)]}
# Revalidate new scientific proof dependencies; historical scope decisions are
# reviewed as bound prior findings, not falsely called newly rerun experiments.
for key in ['capacity','closure','quality','binary_diagnosis']:
 assert all(sha(p)==h for p,h in docs[key]['bindings'].items())
for key in ['signature']:
 p=Path(docs[key]['results']);assert sha(p)==docs[key]['results_sha256'];bindings[str(p)]=sha(p)
cap=docs['capacity'];assert cap['full_NETs']==55300 and cap['full_connections']==115572 and cap['overused_CHANNELs']==0 and cap['all_selected_paths_original_budget_qualified'];assert all(r['fixed_domain_UNSAT_certified'] for r in docs['closure']['rows']);quality=docs['quality'];assert not quality['necessary_case01_gate_pass'] and quality['comparisons']['raw_min_on']['necessary_comparison_pass'] and not quality['comparisons']['previous_native']['necessary_comparison_pass']
# Bind the paid B-bank timing to the exact frozen bank source used by repair.
cost=docs['bank_cost'];membership=docs['bank_membership'];bank_rows=[]
for item in docs['bank_plan']['cases']:
 case=item['case'];frame=Path(item['candidate_B']);receipt=frame.with_name('receipt.json');r=json.loads(receipt.read_text());assert cost['bindings'][str(receipt)]==sha(receipt);assert r['files'][str(frame)]==sha(frame)==membership['bindings'][str(frame)];row=next(x for x in cost['cases'] if x['case']==case);assert abs(row['internal_pre_receipt_serialization_sample_seconds']-r['total_paid_resident_seconds'])<1e-9;original=next(x for x in docs['bank_producer']['cases'] if x['case']==case);assert row['returned_complete_predict_seconds']==original['result']['total_paid_resident_seconds'];assert sha(paths['bank_producer'])==cost['bindings'][str(paths['bank_producer'])];bindings[str(receipt)]=sha(receipt);bindings[str(frame)]=sha(frame)
 bank_rows.append({'case':case,'B_frame':str(frame),'B_returned_predict_seconds':row['returned_complete_predict_seconds'],'B_workspace_seconds':row['compiled_workspace_setup_seconds'],'B_primary_search_seconds_nested':row['primary_search_seconds'],'control_native_plus_canonical_partial_seconds':row['cold_two_recorded_phases_sum_seconds']})
assert abs(sum(x['B_returned_predict_seconds']+x['B_workspace_seconds'] for x in bank_rows)+cost['shared_graph_setup_seconds']-cost['sum_shared_graph_workspace_and_predict_return_seconds'])<1e-8
stop=docs['joint_decision']['stop_loss'];now=datetime.datetime.now(datetime.timezone.utc);deadline=datetime.datetime.fromisoformat(stop['review_no_later_than_utc']);assert now<deadline
review={
 'status':'INTERIM_RESEARCH_DIRECTION_REVIEW_NO_PROMOTABLE_COST_ACCEPTABLE_CANDIDATE',
 'created_utc':now.isoformat(),'stop_loss':stop,'review_deadline_reached':False,
 'what_was_achieved':{'complete_one_case_model_budget_and_CHANNEL_capacity':True,'full_NETs':55300,'full_connections':115572,'checked_CHANNELs':258720,'scope':'Raw model, exposed case01; no native/canonical/STA or independent family admission.'},
 'unresolved_requirements':{'all3_capacity':False,'necessary_previous_native_quality':False,'original_full9_quality':False,'matched_complete_net_gain':False,'cost_acceptable_candidate':False,'strict_unseen':0},
 'candidate_quality_decision':quality['comparisons'],
 'exact_quality_error_accounting':docs['binary_diagnosis'],
 'paid_bank_dependency':{'case_rows':bank_rows,'three_case_B_shared_workspace_predict_subtotal_seconds':cost['sum_shared_graph_workspace_and_predict_return_seconds'],'B_original_process_seconds_interval':[cost['whole_original_producer_wall_seconds_lower'],cost['whole_original_producer_wall_seconds_upper']],'excludes':['A acquisition','new capacity repair','new repair audits','new quality evaluation','downstream candidate native/canonical stages'],'accounting_rule':'Feedback/search durations are nested in returned prediction, not additive. New repair is downstream of frozen A/B acquisition; cached B is not free inference. These measurements are observed historical scopes, not a lower bound on every future redesigned predictor.'},
 'new_repair_scope':{'producer_seconds':docs['joint_run']['total_seconds'],'reused_queries':38,'new_queries':5,'timing_starts_after_input_validation':True,'complete_matched_control_available':False},
 'cost_acceptance_definition':'Use a frozen identical workload, architecture and source states; include startup/input validation, fresh or explicitly paid graph preparation, complete A/B generation if required, repair, admission/audits and downstream native/canonical work. Charge training/offline setup separately with an empirically demonstrated reuse denominator. Accept only verified positive end-to-end difference under the unchanged quality/legality gates. Native+canonical subtotals are not a full control; no speed ratio inferred.',
 'directions':[
  {'direction':'Further peripheral NET expansion or larger CBS bounds within closed domains','decision':'REJECT_FOR_CURRENT_DOMAINS','reason':'Independent monotone branch closure proves those exact domains cannot be repaired; larger search is redundant. Adding new NETs changes the problem but does not repair candidate quality or bank acquisition cost.'},
  {'direction':'Capacity solver as a prediction objective','decision':'NOT_PROMOTED','reason':'One complete capacity-qualified model candidate fails a necessary previous-native quality comparison. Feasibility is a constraint, not an identified native-demand likelihood.'},
  {'direction':'Reweight existing category counts, old-owner pressure, schedule, budgets or ridge confidence','decision':'NO_UNREGISTERED_REPEAT','reason':'Prior negative studies and exact signature aliasing already bound these hypotheses. Independent normalization/flow correctness did not produce all3 original quality acceptance. No threshold/regularization/seed rescue sweep.'},
  {'direction':'A distinct input-derived path/topology signal for correction direction','decision':'REQUIRES_NEW_IDENTIFIABLE_INFORMATION_BEFORE_FITTING','reason':'Existing signatures alias beneficial and harmful changes, and prior ridge/frequency models do not satisfy original all3 gates. A new hypothesis must name information absent from prior geometry/owner/context features and demonstrate train/evaluation namespace separation. No such validated hypothesis is established by this review.'},
  {'direction':'Reuse exact raw duals, physical tree and resource conflict proofs as infrastructure','decision':'RETAIN_FUNCTIONAL_ARTIFACTS_ONLY','reason':'Verified solver/proof components are useful evidence but do not by themselves justify prediction, FPGA performance or continuous-workflow speed claims.'}
 ],
 'remaining_window_work':'Assess the physical/native model and candidate objective mismatch from existing bound evidence, and require a prospective input-only information/cost rationale before any new capacity expansion or training. Preserve the negative quality result and case01 functional candidate. At the original deadline, if no capacity-qualified cost-acceptable candidate exists, stop the broader joint-capacity extension and finalize direction review. No clock reset or automatic model promotion.',
 'excluded_claims':['Full RR infeasibility','All alternative predictors impossible','Capacity candidate is a quality pass','Cold partial baseline is complete workflow time','Cached bank generation is free','Existing MMC layouts are unseen'],
 'historical_evidence_scope':'Bound prior decisions reviewed; not every historical raw route/model reexecuted. Fresh new proof bindings and exact B receipt/frame cost provenance independently rechecked in this script.',
 'bindings':bindings}
p=D/'review.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(review,indent=2)+'\n');tmp.replace(p);print(json.dumps({'status':review['status'],'B_predict_seconds':[r['B_returned_predict_seconds'] for r in bank_rows],'B_component_subtotal':cost['sum_shared_graph_workspace_and_predict_return_seconds'],'deadline':stop['review_no_later_than_utc']},indent=2))
