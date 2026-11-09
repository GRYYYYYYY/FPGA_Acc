"""Generate draft numbers from frozen evidence; no completion certification."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out = root / 'paper'
out.mkdir(exist_ok=True)
sources = {}


def read(relative):
    path = root / relative
    sources[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return json.loads(path.read_text())


potter_source = read('work/potter_primary_source_review_20261018/review.json')
assert potter_source['commit'] == '19b898ab77c13fc88646992e789aa2211626a123'
for path, expected in potter_source['source_sha256'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path

rwroute_docs = read('work/rwroute_official_documentation_review_20261018/review.json')
assert rwroute_docs['http_status'] == 200
for path, expected in rwroute_docs['source_sha256'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path

higher_g_platform = read('work/native_higher_g_hw_emu_link_20261015/group_audit/audit.json')
assert higher_g_platform['status']=='sharded_groups_verified_runtime_ownership_pending'
commit_path = read('work/native_commit_fsm_path_diagnosis_20261015/independent_audit.json')
assert commit_path['fsm']['states']==2496 and commit_path['fsm']['all_state_parameters_one_hot']
assert commit_path['critical_path']['data_delay_ns']==5.235 and commit_path['critical_path']['logic_levels']==13
assert commit_path['critical_path']['route_percent']==77.515
narrow_error_CPU = read('work/native_commit_narrow_error_variant_20261015/independent_audit.json')
assert narrow_error_CPU['status']=='isolated_uint8_internal_error_all75_flat_sharded_differential_calls_pass'
assert narrow_error_CPU['fail_call_sites']==56 and max(narrow_error_CPU['status_codes'].values())==8

narrow_error_synthesis = read('work/native_commit_narrow_error_hls_20261015/synthesis_interim_audit.json')
assert narrow_error_synthesis['timing_warning']['estimate_ns'] > narrow_error_synthesis['timing_warning']['effective_budget_ns']
assert not narrow_error_synthesis['adopted']

narrow_error_RTL = read('work/native_commit_narrow_error_hls_20261015/independent_audit.json')
assert narrow_error_RTL['rtl_calls']==75 and narrow_error_RTL['matching_port_declarations']==290 and narrow_error_RTL['matching_bus_parameters']==79
assert narrow_error_RTL['store_error_argument_bits']==8 and not narrow_error_RTL['adopted']

branch_boundary_synthesis = read('work/native_commit_branch_check_synthesis_20261015/interpretation.json')
assert branch_boundary_synthesis['helper_cycles']==2 and branch_boundary_synthesis['helper_II']==1
assert branch_boundary_synthesis['estimate_ns'] > branch_boundary_synthesis['effective_budget_ns'] and not branch_boundary_synthesis['adopted']

identity_XRT_search = read('work/native_identity_higher_g_xrt_pipeline_20261015/search_stage_audit.json')
assert identity_XRT_search['result_words'][:2]==[0,43] and len(identity_XRT_search['byte_comparisons'])==7

six_phase_synthesis = read('work/native_commit_phase_synthesis_20261015/independent_audit.json')
assert six_phase_synthesis['external_ABI_matches_parent'] and six_phase_synthesis['effective_timing_gate_pass']
assert len(six_phase_synthesis['modules'])==7 and six_phase_synthesis['modules'][0]['fsm_bits']==151

two_phase_synthesis = read('work/native_commit_two_phase_synthesis_20261015/independent_audit.json')
assert two_phase_synthesis['external_ABI_matches_parent'] and two_phase_synthesis['effective_timing_gate_pass']
assert two_phase_synthesis['modules'][0]['resources']['LUT']==165286 and two_phase_synthesis['modules'][0]['fsm_bits']==145
phase_area_growth = read('work/native_commit_phase_synthesis_20261015/area_growth_audit.json')
assert phase_area_growth['total_delta']['LUT']==103608

six_phase_RTL = read('work/native_commit_phase_rtl_20261015/independent_audit.json')
assert six_phase_RTL['rtl_calls']==75 and six_phase_RTL['external_ABI_matches_parent']

two_phase_RTL = read('work/native_commit_two_phase_rtl_20261015/independent_audit.json')
assert two_phase_RTL['rtl_calls']==75 and two_phase_RTL['external_ABI_matches_parent'] and two_phase_RTL['effective_timing_gate_pass']
actual_XRT_path_two_phase_commit = read('work/native_two_phase_XRT_path_CPU_commit_20261015/independent_audit.json')
assert actual_XRT_path_two_phase_commit['commit_calls']==1 and actual_XRT_path_two_phase_commit['query_calls']==42
assert len(actual_XRT_path_two_phase_commit['compared_poststate_files'])==6

identity_XRT_bounded = read('work/native_identity_higher_g_xrt_pipeline_20261015/bounded_outcome_audit.json')
assert identity_XRT_bounded['wall_bound_seconds']==1800 and identity_XRT_bounded['passed_search_artifacts']==7

XRT_argument_contract = read('work/native_XRT_commit_argument_contract_20261015/independent_audit.json')
assert len(XRT_argument_contract['pointer_arguments'])==17 and len(XRT_argument_contract['scalar_arguments'])==12
assert XRT_argument_contract['recorded_nonoverlapping_snapshot_BOs']==15
first_commit_wait = read('work/native_XRT_first_commit_wait_observation_20261015/independent_audit.json')
assert first_commit_wait['last_stage']['name']=='kernel_wait_begin' and first_commit_wait['last_stage']['a']==3
SB3_net_wl = read('work/sb_precision_per_net_wirelength_v3_20261015/independent_audit.json')
SB3_wl_rule = read('work/sb_precision_per_net_wirelength_v3_20261015/interpretation.json')
assert len(SB3_net_wl['outcomes'])==6 and [r['native_wirelength_delta'] for r in SB3_wl_rule['rows'][:2]]==[640,590]

XRT_stage_terminal = read('work/native_identity_XRT_commit_stage_diagnostic_20261015/independent_bounded_audit.json')
XRT_stage_interpretation = read('work/native_identity_XRT_commit_stage_diagnostic_20261015/interpretation.json')
assert XRT_stage_terminal['guard_seconds']==1800 and len(XRT_stage_terminal['search_raw_comparisons'])==7
assert XRT_stage_terminal['last_stage']['name']=='kernel_wait_begin'
large_traffic_RTL = read('work/native_commit_42path_256reads_RTL_diagnostic_v2_20261015/independent_audit.json')
large_traffic_IDs = read('work/native_commit_large_traffic_RTL_identifier_audit_20261015/independent_audit.json')
assert large_traffic_RTL['RTL_calls']==45 and large_traffic_RTL['readset']==256 and large_traffic_RTL['path_nodes']==42
assert len(large_traffic_IDs['modules'])==39 and not large_traffic_IDs['unresolved'] and all(large_traffic_IDs['negative_controls'].values())

commit_logical = read('work/native_commit_logical_access_profile_20261015/independent_audit.json')
assert commit_logical['total_proposal_overlay_key_tests']==7099
key_filter_CPU = read('work/native_commit_key_filter_variant_20261015/independent_audit.json')
key_filter_binding = read('work/native_commit_key_filter_variant_20261015/source_binding_audit.json')
key_filter_plain = read('work/native_commit_key_filter_variant_20261015/plain_native_audit.json')
assert key_filter_CPU['logical_key_tests_before']==7099 and key_filter_CPU['logical_key_tests_after']==967
assert key_filter_CPU['suite_calls']==150 and key_filter_CPU['native_calls']==86
key_filter_RTL = read('work/native_commit_key_filter_HLS_20261015/independent_audit.json')
key_filter_timing = read('work/native_commit_key_filter_HLS_20261015/exact_timing_audit.json')
assert sum(v['RTL_calls'] for v in key_filter_RTL['suites'])==120
assert key_filter_timing['status']=='functional120_pass_numeric_effective_timing_failed'
assert all(not v['reported_estimate_pass'] and not v['warning_emitted'] for v in key_filter_timing['suites'])

two_phase_filter_synthesis = read('work/native_commit_two_phase_key_filter_screen_v2_20261015/independent_audit.json')
two_phase_filter_native = read('work/native_two_phase_filter_full_native_CPU_20261015/independent_audit.json')
assert not two_phase_filter_synthesis['reported_estimate_pass']
assert two_phase_filter_native['native_calls']==86

filter_hierarchy = read('work/native_filter_timing_hierarchy_diagnosis_20261015/independent_audit.json')
filter_probe_screen = read('work/native_commit_filter_probe_pipeline_screen_20261015/independent_audit.json')
filter_probe_structure = read('work/native_commit_filter_probe_pipeline_screen_20261015/structure_audit.json')
assert not filter_probe_screen['reported_estimate_pass']
assert filter_probe_structure['helper_latency']==2 and filter_probe_structure['helper_II']==1
assert filter_probe_structure['top_estimated_ns']=='2.586'

zero_seed_ex5p = read('work/sb_ex5p_zero_seed_interim_20261015/independent_audit.json')
assert len(zero_seed_ex5p['outcomes'])==1
assert zero_seed_ex5p['outcomes'][0]['wirelength']==11752 and not zero_seed_ex5p['outcomes'][0]['joint_gate_pass']

native_zero_length_prices = read('work/native_zero_length_indexed_cost_profile_20261015/independent_audit.json')
assert len(native_zero_length_prices['outcomes'])==3
assert all(v['positive_base_zero_length_nodes']==271224 for v in native_zero_length_prices['outcomes'])

zero_seed_terminal = read('work/rr_remaining_tail_zero_seed_ablation_20261015/independent_audit.json')
zero_seed_comparison = read('work/rr_remaining_tail_zero_seed_ablation_20261015/comparison_audit.json')
zero_seed_conclusion = read('work/rr_remaining_tail_zero_seed_ablation_20261015/interpretation.json')
assert len(zero_seed_terminal['outcomes'])==3
assert zero_seed_conclusion['joint_passes']=={'weight0':1,'weight128':2}

potential8_storage = read('work/native_potential8_lossless_storage_20261015/independent_audit.json')
assert potential8_storage['nodes']==91975782 and potential8_storage['maximum']==42
assert potential8_storage['logical_payload_bytes_saved']==643830472

potential8_kernel_CPU = read('work/native_potential8_kernel_Cmodel_20261015/independent_audit.json')
assert potential8_kernel_CPU['raw_files_per_mode']==7 and potential8_kernel_CPU['flags']==[0,1]
assert potential8_kernel_CPU['sanitizers_pass'] and potential8_kernel_CPU['invalid_flag_rejected']

potential_dual_CPU = read('work/native_potential_dual_format_Cmodel_20261015/independent_audit.json')
assert potential_dual_CPU['legacy_directed_calls']==20 and potential_dual_CPU['wide_fallback256_and_infinity']
assert potential_dual_CPU['sanitizers_pass'] and potential_dual_CPU['raw_files_per_mode']==7

potential_dual_RTL = read('work/native_potential_dual_format_HLS_20261015/independent_audit.json')
assert potential_dual_RTL['RTL_calls']==25 and potential_dual_RTL['reported_estimate_pass']
assert potential_dual_RTL['external_port_declarations']==290 and potential_dual_RTL['bus_parameters']==79

dual_snapshot_XO = read('work/native_dual_potential_hw_emu_review_v2_20261015/compiled_XO_review.json')
dual_XRT_host_preflight = read('work/native_dual_potential_XRT_pipeline_20261015/host_preflight_audit.json')
assert dual_snapshot_XO['compile_reused'] and dual_snapshot_XO['arguments']==15 and dual_snapshot_XO['ports']==7
assert dual_XRT_host_preflight['device_context_not_reached'] and dual_XRT_host_preflight['original_eligible_edges_checked']==212892069

capacity_delay_bound = read('work/sb3_ex5p_capacity_delay_bound_20261015/independent_audit.json')
capacity_delay_certificate = read('work/sb3_ex5p_capacity_delay_bound_20261015/certificate_audit.json')
assert [v['certified_relaxed_optimum_ps'] for v in capacity_delay_certificate['outcomes']]==[644,729]
assert all(v['baseline_packed_delay_unattainable_with_other612nets_fixed'] for v in capacity_delay_certificate['outcomes'])

packed_XRT_search_stage = read('work/native_dual_potential_XRT_search_stage_20261015/independent_audit.json')
occupied_frontier = read('work/sb3_ex5p_delay_frontier_20261015/independent_audit.json')
occupied_frontier_rebuild = read('work/sb3_ex5p_delay_frontier_20261015/frontier_rebuild_audit.json')
single_owner_release = read('work/sb3_ex5p_single_owner_release_20261015/result.json')
assert packed_XRT_search_stage['result_words']==[0,43,256,258,214,256,257,0]
assert packed_XRT_search_stage['potential_format']==2 and packed_XRT_search_stage['packed_payload_bytes']==91975784
assert not packed_XRT_search_stage['commit_completed'] and packed_XRT_search_stage['verified_total_upload_bytes'] is None
assert [v['frontier_nodes'] for v in occupied_frontier_rebuild['outcomes']]==[31,29]
assert [v['single_owner_target_successes'] for v in single_owner_release['outcomes']]==[2,1]

owner_search_small = read('work/single_owner_exchange_search_checks_20261015/audit.json')
owner_search_boundary = read('work/single_owner_exchange_boundary_checks_20261015/audit.json')
owner_search_potential = read('work/sb3_augmented_owner_search_potential_20261015/result.json')
owner_suffix_certificate = read('work/sb3_owner_search_suffix_certificate_20261015/independent_audit.json')
owner_exchange_private = read('work/sb3_ex5p_two_net_exchange_v2_20261015/independent_audit.json')
owner_exchange_native = read('work/sb3_ex5p_two_net_native_validation_v2_20261015/result.json')
owner_exchange_interpretation = read('work/sb3_ex5p_two_net_native_validation_v2_20261015/interpretation.json')
packed_XRT_terminal = read('work/native_dual_potential_XRT_pipeline_20261015/independent_outcome_audit.json')
assert owner_search_small['random_graphs']==500 and owner_search_boundary['cases']==2000
assert [v['expanded'] for v in owner_search_potential['outcomes']]==[109,142]
assert sum(v['complete'] for v in owner_exchange_private['outcomes'])==38
assert len(owner_exchange_native['outcomes'])==len(owner_exchange_interpretation['outcomes'])==3
assert all(v['legal'] and not v['joint_WL_CPD_baseline_pass'] for v in owner_exchange_interpretation['outcomes'])
assert not packed_XRT_terminal['completed'] and packed_XRT_terminal['terminal']['reason']=='predeclared_diagnostic_wall_bound'
assert not packed_XRT_terminal['wait_returns'] and not packed_XRT_terminal['wait_exceptions']

exchange_wire_decomposition = read('work/sb3_ex5p_two_net_native_validation_v2_20261015/wirelength_decomposition.json')
constrained_wire_small = read('work/delay_bounded_wire_search_checks_20261015/audit.json')
constrained_wire_fixed = read('work/sb3_delay_bounded_displaced_repair_20261015/independent_audit.json')
exchange_native_observation = read('work/sb3_native_exchange_timing_observation_20261015/result.json')
exchange_observation_checks = read('work/sb3_native_exchange_timing_observation_20261015/observation_checks.json')
STA_budget_repairs = read('work/sb3_STA_budget_displaced_repair_20261015/result.json')
STA_budget_native = read('work/sb3_STA_budget_repair_native_20261015/result.json')
STA_budget_interpretation = read('work/sb3_STA_budget_repair_native_20261015/interpretation.json')
assert constrained_wire_small['cases']==1000
assert sum(v['orders'] for v in constrained_wire_fixed['outcomes'])==14 and constrained_wire_fixed['new_native_runs']==0
assert len(exchange_native_observation['outcomes'])==3 and all(v['connections_observed']==1920 and v['native_qor_unchanged'] for v in exchange_native_observation['outcomes'])
assert len(STA_budget_repairs['outcomes'])==len(STA_budget_native['outcomes'])==14
assert STA_budget_native['distinct_native_runs']==len(STA_budget_interpretation['outcomes'])==6
assert all(v['legal'] and v['cpd_delta_from_exchange_ns']==0 and not v['joint_baseline_pass'] for v in STA_budget_interpretation['outcomes'])
STA_budget_best=min(STA_budget_interpretation['outcomes'],key=lambda v:(v['cpd_ns'],v['wirelength']))

joint_budget_small = read('work/delay_crossing_bounded_wire_checks_20261015/audit.json')
shared_tree_budget_checks = read('work/shared_tree_budget_repair_checks_20261015/audit.json')
first_crossing_probe = read('work/first_crossing_rejection_repair_20261015/result.json')
first_crossing_native = read('work/first_crossing_rejection_repair_20261015/native_review/result.json')
slack_first_WL_checkpoint = read('work/native_slack_repair_first_WL_milestone_20261015/audit.json')
assert joint_budget_small['cases']==1500 and shared_tree_budget_checks['random_graphs']==400
assert first_crossing_probe['result']['complete'] and first_crossing_probe['result']['crossings']<=first_crossing_probe['crossing_allowance']
assert first_crossing_native['native_wirelength']==11636 and first_crossing_native['parent_wirelength']==11643
assert first_crossing_native['native_cpd_ns']==first_crossing_native['parent_cpd_ns']==10.5998
assert not first_crossing_native['joint_baseline_pass']
assert slack_first_WL_checkpoint['wirelength']<=slack_first_WL_checkpoint['baseline_wirelength'] and slack_first_WL_checkpoint['cpd_ns']>slack_first_WL_checkpoint['baseline_cpd_ns']

gpu_body_review = read('work/gpu_primary_fulltext_retry_20261016/review.json')
assert gpu_body_review['status']=='selected_GPU_primary_body_sections_reviewed'
lookahead_method_review = read('work/multidie_lookahead_method_comparison_20261016/comparison.json')
assert lookahead_method_review['status']=='bounded_primary_method_and_current_source_comparison'
refreshed_plot = read('paper/figures/refreshed_native_quality.json')
assert refreshed_plot['status']=='audited_v2_and_refreshed_quality_figure_rendered'
refreshed_policy = read('work/native_refreshed_critical_policy_v1_20261016/independent_audit.json')
assert refreshed_policy['status']=='three_refreshed_policy_cases_selection_budgets_native_decisions_and_final_connectivity_replayed'
refreshed_cases={r['case']:r for r in refreshed_policy['outcomes']}
assert set(refreshed_cases)=={'ex5p','diffeq','alu4'} and all(r['joint_baseline_pass'] for r in refreshed_cases.values())
compound_cost = read('work/native_compound_cost_coverage_20261016/audit.json')
assert not any(r['total_wall_time_established'] for r in compound_cost['cases'])
compound_repeat = read('work/native_instrumented_compound_repeat_review_20261016/independent_audit.json')
assert compound_repeat['status']=='compound_repeat_stage_replays_and_final_comparison_complete'
assert len(compound_repeat['comparisons'])==3 and all(r['final_tree_identical'] and r['quality_identical'] for r in compound_repeat['comparisons'])
compound_timing = read('work/native_instrumented_compound_timing_review_20261016/audit.json')
assert compound_timing['status']=='terminal_compound_stage_and_case_timing_partitions_checked'
adaptive_compound = read('work/native_adaptive_compound_review_20261017/independent_audit.json')
assert adaptive_compound['status']=='actual_adaptive_parent_plus_quality_refinement_reviewed' and adaptive_compound['same_tree_as_serial_compound']
assert adaptive_compound['quality']['legal'] and adaptive_compound['crossings']==refreshed_cases['ex5p']['crossings']
assert adaptive_compound['quality']['total_wirelength']==refreshed_cases['ex5p']['wirelength'] and adaptive_compound['quality']['critical_path_delay_ns']==refreshed_cases['ex5p']['cpd_ns']
migration_pair = read('work/three_layer_migration_native_pair_review_20261016/independent_audit.json')
assert migration_pair['status']=='ten_same_graph_migration_runs_integrity_repeat_and_native_quality_reviewed'
assert all(len(rows)==5 and not any(r['joint_baseline_pass'] for r in rows) for rows in migration_pair['outcomes'].values())
integrated_route_terminal = read('work/integrated_control_route_failure_terminal_20261016/audit.json')
assert integrated_route_terminal['link_returncode']==1 and integrated_route_terminal['failed_signals']==2827 and integrated_route_terminal['node_overlaps']==2112
lean_start = read('work/native_start_validate_only_HLS_v2_20261016/independent_audit.json')
assert lean_start['status']=='paired_HLS_CSIM_ABI_and_resources_reviewed'
assert all(r['estimated_clock_pass'] for r in lean_start['outcomes'])
lean_start_rtl = read('work/native_start_validate_only_RTL_20261017/independent_audit.json')
assert lean_start_rtl['status']=='lean_start75_Verilog_calls_exact_numeric_gate_and_ABI_verified' and lean_start_rtl['RTL_calls']==75
lean_start_xo = read('work/lean_start_actual_XO_comparison_20261017/audit.json')
assert lean_start_xo['status']=='actual_hw_XO_matches_paired_HLS_area_ABI_and_validation_only_helper'
assert lean_start_xo['resource_delta']==lean_start['resource_delta']
current_claims = read('work/current_research_claim_matrix_v2_20261017/matrix.json')
assert len(current_claims['gates'])==8 and not any(g['completion_proven'] for g in current_claims['gates'])
for path,h in current_claims['archived_inputs_sha256'].items():
    assert hashlib.sha256((root/path).read_bytes()).hexdigest()==h,path
slack_cohort_complete = read('work/native_slack_guided_net_repair_v1_20261015/independent_audit.json')
assert slack_cohort_complete['status']=='three_development_sweeps_native_decisions_and_final_connectivity_independently_replayed'
slack_cohort_cases={r['case']:r for r in slack_cohort_complete['outcomes']}
assert set(slack_cohort_cases)=={'ex5p','diffeq','alu4'}
assert sum(r['joint_baseline_pass'] for r in slack_cohort_cases.values())==2
slack_ex5p_complete = read('work/native_slack_guided_net_repair_v1_20261015/ex5p_case_independent_audit.json')
assert len(slack_ex5p_complete['outcomes'])==1
slack_ex5p_final=slack_ex5p_complete['outcomes'][0]
assert slack_ex5p_final['nets_visited']==613 and slack_ex5p_final['accepted']==56 and slack_ex5p_final['native_calls']==174
assert not slack_ex5p_final['joint_baseline_pass']

admission_stage_CPU = read('work/native_admission_compare_stage_CPU_20261015/independent_audit.json')
admission_stage_HLS = read('work/native_admission_compare_stage_HLS_screen_20261015/independent_audit.json')
admission_stage_RTL = read('work/native_admission_compare_stage_RTL_20261015/independent_audit.json')
admission_stage_native = read('work/native_admission_compare_stage_full_native_CPU_20261015/independent_audit.json')
two_phase_XRT_search = read('work/native_two_phase_XRT_search_stage_20261015/independent_audit.json')
assert admission_stage_CPU['tuple_cases']==100000 and admission_stage_CPU['UBSan_pass']
assert admission_stage_RTL['RTL_calls']==10 and admission_stage_RTL['helper_latency_cycles']==2 and admission_stage_RTL['helper_II']==1
assert len(admission_stage_native['outcomes'])==2 and all(len(v['raw_files'])==7 for v in admission_stage_native['outcomes'])
assert len(two_phase_XRT_search['artifacts'])==7 and not two_phase_XRT_search['commit_completed']

split_start_CPU = read('work/native_commit_split_start_CPU_20261015/independent_audit.json')
split_start_HLS = read('work/native_commit_split_start_HLS_screen_20261015/recovered_independent_audit.json')
split_start_RTL = read('work/native_commit_split_start_RTL_20261015/independent_audit.json')
split_start_native = read('work/native_commit_split_start_full_native_CPU_20261015/independent_audit.json')
admission_worker_RTL = read('work/native_admission_compare_stage_worker_RTL_20261015/independent_audit.json')
integrated_control_CPU = read('work/native_integrated_control_stages_CPU_20261015/independent_audit.json')
integrated_control_compile = read('work/native_integrated_control_compiled_audit_20261015/independent_audit.json')
two_phase_XRT_terminal = read('work/native_two_phase_identity_XRT_pipeline_20261015/independent_outcome_audit.json')
assert split_start_CPU['calls_per_flag']==75 and split_start_RTL['RTL_calls']==75
assert split_start_native['calls_per_flag']==43 and split_start_native['raw_files_per_flag']==6
assert admission_worker_RTL['RTL_calls']==22 and admission_worker_RTL['equal_f_subset_calls']==8
assert len(integrated_control_CPU['artifacts'])==13
assert len(integrated_control_compile['components'])==3 and not integrated_control_compile['physical_timing_pass']
assert not two_phase_XRT_terminal['completed'] and not two_phase_XRT_terminal['wait_returns']
assert two_phase_XRT_terminal['terminal']['reason']=='predeclared_diagnostic_wall_bound'

two_phase_physical = read('work/two_phase_routed_independent_review_20261015/independent_audit.json')
assert two_phase_physical['design_timing_summary']['wns_ns']==-1.362
assert two_phase_physical['design_timing_summary']['setup_failing']==36121
assert two_phase_physical['route']['fully_routed']==two_phase_physical['route']['routable']==583626
assert not two_phase_physical['checks']['setup'] and all(v for k,v in two_phase_physical['checks'].items() if k!='setup')

fixed_feedback = read('work/sb3_fixed_feedback_pair_20261015/independent_audit.json')
fixed_feedback_comparison = read('work/sb3_fixed_feedback_pair_20261015/comparison_audit.json')
fixed_feedback_interpretation = read('work/sb3_fixed_feedback_pair_20261015/interpretation.json')
assert len(fixed_feedback['outcomes'])==6
assert fixed_feedback_comparison['feedback_off_joint_passes']==fixed_feedback_comparison['feedback_on_joint_passes']==2
assert not fixed_feedback_interpretation['adopted']

terminal_trajectory = read('work/sb_ex5p_task895_timing_trajectory_20261015/independent_audit.json')
terminal_policy = read('work/sb_ex5p_terminal_timing_policy_20261015/independent_audit.json')
assert [v['observed_terminal_task_would_cross_cap'] for v in terminal_policy['outcomes']]==[True,False]

critical_RR = read('work/sb_ex5p_critical_arc_RR_binding_v5_20261015/independent_audit.json')
critical_capacity = read('work/sb_ex5p_critical_route_capacity_v3_20261015/independent_audit.json')
assert [v['blocked_baseline_nodes'] for v in critical_capacity['outcomes']]==[5,8]
assert all(v['all_resource_occupancies_rebuilt']==336312 for v in critical_capacity['outcomes'])
assert all(not v['baseline_path_capacity_feasible_with_other_nets_fixed'] for v in critical_capacity['outcomes'])

native_STA_paths = read('work/sb_ex5p_native_STA_path_alignment_20261015/independent_audit.json')
native_STA_interpretation = read('work/sb_ex5p_native_STA_path_alignment_20261015/interpretation.json')
native_STA_plot = read('paper/figures/ex5p_native_endpoint_arrivals.json')
assert [v['higher_printed_arrival_endpoints'] for v in native_STA_interpretation['observations']]==[50,59]
assert all(len(v)==63 for v in native_STA_paths['paths'].values())
for filename,digest in native_STA_plot['artifacts'].items():
    assert hashlib.sha256(Path(filename).read_bytes()).hexdigest()==digest

precision_terminal = read('work/rr_remaining_tail_precision_development_v2_20261015/independent_audit.json')
precision_conclusion = read('work/rr_remaining_tail_precision_development_v2_20261015/interpretation.json')
assert len(precision_terminal['outcomes'])==6 and precision_conclusion['passes_by_scale']=={'scale1':2,'scale256':2}
assert precision_conclusion['total_parent_comparisons']==115
identity_preparation = read('work/native_policy_identity_hop_bound_20261015/independent_audit.json')
assert identity_preparation['eligible_edges']==212892069 and identity_preparation['source_potential']==42
assert identity_preparation['serialized_bytes']==2691084180 and identity_preparation['preparation_BFS_expanded']==31308452
identity_ordering = read('work/native_policy_identity_ordering_cpu_20261015/independent_audit.json')
assert [v['expanded'] for v in identity_ordering['panel']]==[229746,58069,1907,43]
identity_commit = read('work/native_identity_higher_g_commit_differential_20261015/independent_audit.json')
assert identity_commit['canonical_reads']==256 and identity_commit['differential_calls']==43 and identity_commit['all_net_trees_checked']==341
identity_top = read('work/native_identity_higher_g_top_cmodel_20261015/independent_audit.json')
assert len(identity_top['artifact_comparisons'])==7 and identity_top['worker_fixture_calls']==8
higher_g_HLS = read('work/native_higher_g_hls_validation_20261015/independent_audit.json')
assert len(higher_g_HLS['components'])==2 and all(v['verilog_cosim']=='Pass' for v in higher_g_HLS['components'])
const_zero_routed = read('work/const_zero_final_clock_metadata_20261015/independent_audit.json')
assert const_zero_routed['design_timing_summary']['wns_ns']==-2.413 and const_zero_routed['final_clock_topology_mhz']['DATA_CLK']==174
assert not const_zero_routed['adopted']

higher_g_ordering = read('work/native_higher_g_tie_variant_20261015/independent_audit.json')
assert [v['expanded'] for v in higher_g_ordering['outcomes']]==[229746,58069]
assert all(v['cost']==42 and v['path_edges']==42 for v in higher_g_ordering['outcomes'])
assert higher_g_ordering['default_control_artifact_comparisons']==7 and not higher_g_ordering['adopted']
higher_g_commit = read('work/native_higher_g_commit_differential_20261015/independent_audit.json')
assert higher_g_commit['differential_calls']==43 and higher_g_commit['canonical_reads']==180700
assert higher_g_commit['all_net_trees_checked']==341

hw_emu_16 = read('work/native_sharded_quotient_budget16_diagnostic_20261015/independent_audit.json')
assert hw_emu_16['result_words'][1]==16 and hw_emu_16['observations']==63
baseline_reproduction = read('work/native_fullgraph_cpu_full_search_20261015/prior_baseline_reconciliation.json')
assert len(baseline_reproduction['comparisons'])==6
flat_commit_recheck = read('work/native_fullgraph_cpu_full_search_20261015/reused_flat_commit_review/independent_audit.json')
assert flat_commit_recheck['published_nodes']==42 and flat_commit_recheck['all_net_trees_checked']==341
ex5p_precision_interim = read('work/sb_ex5p_remaining_tail_precision_interim_20261015/independent_audit.json')
assert len(ex5p_precision_interim['outcomes'])==2 and all(not v['joint_gate_pass'] for v in ex5p_precision_interim['outcomes'])

cpu_full_search = read('work/native_fullgraph_cpu_full_search_20261015/independent_audit.json')
assert cpu_full_search['result_words'][0]==0 and cpu_full_search['path_edges']==42 and cpu_full_search['selected_path_cost']==42
cpu_full_journal = read('work/native_fullgraph_cpu_full_search_20261015/journal_authority_audit.json')
assert cpu_full_journal['records']==862428 and cpu_full_journal['present_unique_nodes']==0
assert cpu_full_journal['minimum_membership_die_changes']==1
cpu_input_binding = read('work/native_fullgraph_cpu_full_search_20261015/input_binding_completeness.json')
assert len(cpu_input_binding['actual_payloads'])==11
bounded_256 = read('work/native_sharded_quotient_budget256_diagnostic_20261015/bounded_outcome_review.json')
assert not bounded_256['descendants_still_present']
quotient_probe = read('work/native_sharded_quotient_budget1_diagnostic_20261015/independent_audit.json')
assert quotient_probe['expanded']==1 and quotient_probe['host_returncode']==0

tail_weight_terminal = read('work/rr_remaining_tail_seed_weight_development_v2_20261015/independent_audit.json')
assert len(tail_weight_terminal['outcomes']) == 6
assert [sum(r['joint_gate_pass'] for r in tail_weight_terminal['outcomes'] if r['arm']==w) for w in ['weight128','weight256']] == [2,1]
large_workspace_probe = read('work/native_sharded_large_workspace_budget1_diagnostic_20261015/independent_audit.json')
assert large_workspace_probe['host_returncode']==0 and large_workspace_probe['expanded']==1
assert large_workspace_probe['search_status']==2 and not large_workspace_probe['board_result']

fanout_present = read('work/rr_fanout_present_interaction_variant_v2_20261015/independent_audit.json')
assert fanout_present['status']=='twenty_native_fanout_present_runs_independently_reviewed'
assert not fanout_present['outcomes']['present2_fanout1']['all_ex5p_model_checks_pass']
bus_skew_audit = read('work/archived_sharded_bus_skew_audit_20261015/independent_audit.json')
assert bus_skew_audit['status']=='archived_bus_skew_229_numeric_met_one_constraint_NA'
assert bus_skew_audit['numeric_violations']==0 and len(bus_skew_audit['unmeasured_constraints'])==1
api_coverage_terminal = read('work/rr_view_access_coverage_variant_20261015/independent_audit.json')
assert api_coverage_terminal['status']=='ten_native_explicit_api_coverage_runs_integrity_and_counts_reviewed_quality_failed'
assert api_coverage_terminal['covered_repeats']==api_coverage_terminal['control_repeats']==5
assert not api_coverage_terminal['quality']['covered']['joint_quality_pass']
opin_three_layer_failure = read('work/native_layer_capacity_scaling_v2_20261015/structural_unreachability_independent_audit.json')
sb_development_matched = read('work/sb_three_layer_development_matched_20261015/independent_audit.json')
assert sb_development_matched['status']=='six_matched_three_layer_development_runs_independently_reviewed' and len(sb_development_matched['outcomes'])==6
sb_remaining_quality = read('work/sb_three_layer_development_matched_20261015/interpretation.json')
assert not sb_remaining_quality['all_development_gates_pass'] and sb_remaining_quality['candidate_fail_cases']==['ex5p']
sb_quality_plot = read('paper/figures/sb_development_quality.json')
assert sb_quality_plot['status']=='three_case_native_quality_normalized_plot_rendered'
for _file,_hash in sb_quality_plot['artifacts'].items():
    assert hashlib.sha256(Path(_file).read_bytes()).hexdigest()==_hash
    sources[str(Path(_file).relative_to(root))]=_hash
sb_diffeq_interim = read('work/sb_diffeq_three_arm_interim_review_20261015/independent_audit.json')
assert sb_diffeq_interim['status']=='diffeq_three_matched_arms_current_evidence_reviewed'
_diffeq_arms={r['arm']:r for r in sb_diffeq_interim['outcomes']}
assert _diffeq_arms['remaining_tail']['joint_gate_pass'] and _diffeq_arms['flat']['joint_gate_pass']
assert not _diffeq_arms['legacy_downstream']['cpu_legal'] and _diffeq_arms['legacy_downstream']['overused_resources']==24
sb_development_delay_calibration = read('work/sb_development_native_delay_calibration_20261015/independent_audit.json')
assert sb_development_delay_calibration['total_connections']==4060 and len(sb_development_delay_calibration['cases'])==2
assert all(r['maximum_absolute_delay_error_ps']==2 and abs(r['native_minus_local_cpd_ps'])<=1 for r in sb_development_delay_calibration['cases'])
remaining_tail_delay_calibration = read('work/sb_remaining_tail_native_delay_calibration_20261015/independent_audit.json')
assert remaining_tail_delay_calibration['connections']==1920 and remaining_tail_delay_calibration['exact_integer_ps_matches']==1266
assert remaining_tail_delay_calibration['maximum_absolute_delay_error_ps']==2
assert remaining_tail_delay_calibration['native_cpd_ps']==remaining_tail_delay_calibration['local_override_cpd_ps']==10866
remaining_tail_native = read('work/rr_remaining_layer_tail_variant_20261015/interpretation.json')
assert remaining_tail_native['status']=='remaining_layer_tail_pilot_legal_convergence_but_joint_native_quality_failed'
assert remaining_tail_native['wirelength']==12255 and remaining_tail_native['cpd_ns']==10.8661
assert remaining_tail_native['model_crossings']==828 and remaining_tail_native['iterations']==9
sb_development_costs = read('work/sb_development_native_indexed_costs_20261015/independent_audit.json')
assert sb_development_costs['status']=='two_development_native_indexed_cost_maps_and_all_edge_rebases_independently_verified'
assert sb_development_costs['total_node_costs_checked']==672624 and sb_development_costs['total_edges_checked']==1123122
sb_development_roundtrip = read('work/sb_development_roundtrip_preflight_20261015/independent_audit.json')
assert sb_development_roundtrip['status']=='two_development_full_graph_node_edge_and_native_noop_roundtrips_independently_reviewed'
assert sb_development_roundtrip['total_nodes']==672624 and sb_development_roundtrip['total_edges']==1123122
sb_development = read('work/native_sb_three_layer_development_20261015/independent_audit.json')
assert sb_development['status']=='two_remaining_declared_development_baselines_native_legal_exact_same_three_layer_RR_verified'
assert {r['case'] for r in sb_development['cases']}=={'diffeq','alu4'}
assert all(r['native_legal'] and r['rr_nodes']==336312 and r['rr_edges']==561561 for r in sb_development['cases'])
remaining_tail_counterexample = read('work/rr_multihop_tail_counterexample_20261015/audit.json')
remaining_tail_host = read('work/rr_remaining_layer_tail_variant_20261015/host_readiness_audit.json')
remaining_tail_journal = read('work/rr_remaining_layer_tail_variant_20261015/journal_audit.json')
assert remaining_tail_counterexample['hierarchical_cost']==2496 and remaining_tail_counterexample['flat_cost']==384
assert remaining_tail_host['default_off']['parent_artifact_comparisons']==350
assert remaining_tail_host['enabled']['bounded_comparisons']==7200
assert remaining_tail_journal['cases']==8 and remaining_tail_journal['ASAN_UBSAN']
sb_pilot_failure = read('work/sb_three_layer_pilot_failure_review_20261015/independent_audit.json')
assert sb_pilot_failure['status']=='failed_three_layer_pilot_exact_replay_tree_and_overuse_review_complete'
assert sb_pilot_failure['downstream_bounded']['overused_resources']==15 and sb_pilot_failure['replay']['epochs']==30
sb_paths = read('work/sb_native_layer_path_profiles_20261015/audit.json')
assert sb_paths['status']=='six_native_full_tree_multilayer_path_profiles_checked'
assert len(sb_paths['cases'])==6 and all(r['tasks']==1920 for r in sb_paths['cases'])
assert all(r['actual_crossing_hops']==r['minimum_adjacent_layer_hops'] for r in sb_paths['cases'])
multilayer_bounds = read('work/rr_multilayer_bound_equivalence_20261015/audit.json')
assert multilayer_bounds['status']=='three_four_layer_7200_bounded_comparisons_and_2400_BFS_outcomes_verified'
assert multilayer_bounds['result']['graphs']==2400 and multilayer_bounds['result']['bounded_comparisons']==7200
assert multilayer_bounds['result']['reachable']==1194 and multilayer_bounds['result']['unreachable']==1206
sb_indexed_costs = read('work/sb_native_indexed_costs_20261015/independent_audit.json')
assert sb_indexed_costs['status']=='six_native_indexed_cost_maps_and_all_edge_rebases_independently_verified'
assert sb_indexed_costs['total_node_costs_checked']==2441074 and sb_indexed_costs['total_edges_checked']==3747204
sb_roundtrip = read('work/sb_native_roundtrip_preflight_20261015/independent_audit.json')
assert sb_roundtrip['status']=='six_full_graph_node_edge_and_native_noop_roundtrips_independently_reviewed'
assert len(sb_roundtrip['cases'])==6 and sb_roundtrip['total_nodes']==2441074 and sb_roundtrip['total_edges']==3747204
sb_scaling = read('work/native_sb_layer_capacity_scaling_20261015/independent_audit.json')
assert sb_scaling['status']=='six_native_switchblock_layer_capacity_baselines_independently_audited'
assert {(r['layers'],r['channel_width']) for r in sb_scaling['baselines']}=={(l,w) for l in [2,3,4] for w in [80,96]}
sb_three_layer = read('work/native_sb_three_layer_feasibility_20261015/result.json')
assert opin_three_layer_failure['status']=='failed_native_connections_unreachable_in_full_rr_graph'
assert all(not v['target_reachable'] for v in opin_three_layer_failure['failures'])
assert sb_three_layer['status']=='native_sb_feasibility_probe_passed_true_layers_verified'
assert sb_three_layer['baselines'][0]['layers']==3
four_layer_build = read('work/vpr_four_layer_build_20261015/build_dependency_audit.json')
four_layer_compat = read('work/vpr_four_layer_postrun_queue_20261015/two_layer_compatibility_audit.json')
assert four_layer_build['status']=='new_frozen_vpr_sources_compiler_dependencies_and_link_inputs_audited'
assert four_layer_compat['numerical_and_canonical_compatibility'] and len(four_layer_compat['cases'])==5
api_coverage_first = read('work/rr_view_access_coverage_variant_20261015/first_native_api_coverage_review.json')
assert api_coverage_first['status']=='first_native_explicit_api_coverage_and_value_replay_reviewed_repeats_pending'
assert api_coverage_first['proposal_phases']==13950 and api_coverage_first['unique_node_occurrences']==49069223
seed_weight = read('work/rr_fanout_seed_weight_variant_v3_20261015/independent_audit.json')
assert seed_weight['status']=='ten_native_seed_weight_runs_reviewed_joint_quality_failed'
assert all(v['repeats']==5 and not v['joint_quality_pass'] for v in seed_weight['outcomes'].values())
fanout_terminal = read('work/rr_fanout_net_order_variant_20261015/terminal_evidence_review.json')
read_terminal = read('work/rr_read_observation_variant_20261015/terminal_evidence_review.json')
clock_domains = read('work/native_snapshot_sharded_clock_failure_profile_20261015/audit.json')
assert fanout_terminal['verified_referenced_files'] == 85
assert read_terminal['verified_referenced_files'] == 55
assert all(not r['joint_quality_pass'] for r in fanout_terminal['outcomes'].values())
assert all(not r['joint_quality_pass'] for r in read_terminal['outcomes'].values())
clock_rows = {r['clock']:r for r in clock_domains['intra_clock_rows']}
assert clock_rows['hbm_aclk']['setup_failing'] == 365
assert clock_rows['clk_kernel_00_unbuffered_net']['setup_failing'] == 46503
static_placement = read('work/rr_task_migration_variant_20261015/result.json')
assert static_placement['status'] == 'fifteen_static_observer_placement_runs_and_native_quality_audited'
assert static_placement['identical_core_artifacts']
assert all(not row['joint_native_quality_pass'] for row in static_placement['outcomes'].values())
credit_native = read('work/rr_task_credit_queue_variant_20261015/independent_audit.json')
adaptive_native = read('work/rr_adaptive_task_migration_variant_20261015/independent_audit.json')
assert adaptive_native['status'] == 'ten_native_adaptive_migration_runs_independently_audited_quality_gate_still_failed'
assert all(row['repeats'] == 5 and not row['joint_quality_pass'] for row in adaptive_native['outcomes'].values())
credit_protocol = read('work/rr_task_credit_queue_variant_20261015/native_protocol.json')
receiver_native = read('work/rr_task_seed_observation_variant_20261015/independent_audit.json')
assert credit_native['status'] == 'fifteen_native_credit_queue_runs_independently_audited_quality_gate_still_failed'
assert receiver_native['status'] == 'five_native_receiver_seed_runs_independently_audited_quality_gate_still_failed'
assert len(receiver_native['runs']) == 5 and all(r['repeats'] == 5 for r in credit_native['outcomes'].values())
assert all(not r['checks']['wirelength_nondegrade'] and not r['checks']['cpd_nondegrade'] for r in credit_native['outcomes'].values())
initial_pair = read('work/rr_native_initial_criticality_study_20261015/result.json')
initial_decision = read('work/rr_native_initial_criticality_study_20261015/interpretation.json')
initial_join = read('work/ex5p_native_initial_task_join_20261015/audit.json')
target_initial = read('work/initial_lookahead_target_aware_variant_20261018/independent_audit.json')
assert target_initial['attempts'] == target_initial['successful_attempts'] == 5
assert target_initial['exact_direct_query_comparisons'] == 9600 and target_initial['candidate_repeat_artifacts_equal']
assert len(target_initial['rows']) == 5 and all(v['wirelength'] == 9582 and v['cpd_ns'] == 9.61746 and v['zero_initial_delays'] == 79 and not v['joint_parent_quality_pass'] for v in target_initial['rows'])
for path, expected in target_initial['source_sha256'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
initial_runtime = read('work/initial_lookahead_runtime_probe_20261018/independent_audit.json')
assert initial_runtime['status'] == 'all_1920_initial_queries_zero_direct_candidate_and_native_identity_reviewed'
assert initial_runtime['connections'] == initial_runtime['zero_direct_candidate_connections'] == 1920
assert initial_runtime['layer_candidates'] == 3840 and initial_runtime['cross_layer_target_connections'] == 757
assert initial_runtime['initial_csv_byte_equal'] and len(initial_runtime['byte_equal_canonical_outputs']) == 5
for path, expected in initial_runtime['source_sha256'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
assert initial_pair['status'] == 'ten_initial_criticality_runs_native_validations_and_independent_audits_complete'
assert initial_decision['status'] == 'native_initial_criticality_pair_complete_quality_regression_no_adoption'
assert initial_decision['control_parent_artifact_checks'] == 330 and initial_join['tasks'] == 1920
criticality_pair = read('work/rr_criticality_shift_variant_20261015/result.json')
criticality_decision = read('work/rr_criticality_shift_variant_20261015/interpretation.json')
assert criticality_decision['status'] == 'criticality_shift_native_pair_complete_quality_regression_no_adoption'
assert criticality_pair['status'] == 'ten_run_criticality_transform_pair_native_and_independent_state_audits_complete'
persistent_pairs = read('work/vpr_persistent_timing_pairs_20261015/manifest.json')
persistent_pairs_audit = read('work/vpr_persistent_timing_pairs_20261015/independent_audit.json')
persistent_context = read('work/vpr_persistent_timing_pairs_20261015/shared_host_context.json')
assert persistent_pairs['status'] == 'five_alternating_cpu_pairs_complete_all_artifacts_audited'
assert persistent_pairs_audit['status'] == 'five_cpu_pairs_independently_audited'
assert persistent_pairs_audit['artifact_comparisons'] == 660
assert persistent_pairs['paired_ratios'] == persistent_pairs_audit['paired_fresh_over_persistent_ratios']
commit_hls_layouts = read('work/native_commit_hls_layout_profile_v2_20261015/profile.json')
assert commit_hls_layouts['status'] == 'embedded_commit_hls_layout_estimates_profiled'
assert all(k['top_latency_cycles'] is None for k in commit_hls_layouts['kernels'].values())

banked_snapshot = read('work/native_snapshot_sharded_routed_timing_snapshot_20261015/audit.json')
assert banked_snapshot['status']=='live_banked_routed_report_snapshot_setup_failed'
assert banked_snapshot['design_timing_summary']['wns_ns']<0
banked_reports = read('work/native_snapshot_sharded_independent_report_audit_20261015/audit.json')
banked_clock = read('work/native_snapshot_sharded_clock_audit_20261015/audit.json')
banked_groups = read('work/native_snapshot_sharded_hw_v1_20261014/group_audit/audit.json')
assert banked_reports['status'] == 'archived_banked_routed_checkpoint_evidence_audited'
assert banked_clock['status'] == 'hardware_clock_metadata_reextracted_and_matched_to_image'
assert banked_groups['status'] == 'hardware_sharded_final_image_groups_verified_runtime_ownership_pending'
assert banked_reports['xclbin_sha256'] == banked_clock['xclbin_sha256'] == banked_groups['xclbin_sha256']
assert not banked_reports['setup_pass'] and not banked_reports['full_signoff_complete']
assert not banked_reports['kernel_clock_mapping_complete'] and not banked_reports['final_bitstream_correspondence_proven']
assert banked_reports['design_timing_summary']['wns_ns'] == banked_snapshot['design_timing_summary']['wns_ns']
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p,h in banked_reports['source_sha256'].items())
banked_cu_clocks = read('work/native_snapshot_sharded_cu_clock_probe_20261015/manifest.json')
assert banked_cu_clocks['status'] == 'all_three_archived_cu_clock_pins_resolved'
assert banked_cu_clocks['checkpoint_sha256'] == banked_reports['checkpoint_sha256']
assert len(banked_cu_clocks['rows']) == 3
assert {r['cu'] for r in banked_cu_clocks['rows']} == {'net_commit','search_worker','snapshot_search'}
assert all(r['clock'] == 'clk_kernel_00_unbuffered_net' and float(r['period_ns']) == 3.333 for r in banked_cu_clocks['rows'])
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p,h in banked_cu_clocks['source_sha256'].items())
hardware_constraints = read('work/native_snapshot_terminal_report_audit_20261014/constraint_coverage_audit.json')
assert hardware_constraints['status'] == 'routed_report_timing_and_constraint_coverage_extracted'

hardware_clock = read('work/native_snapshot_reference_clock_audit_20261015/audit.json')
hardware_terminal = read('work/native_snapshot_terminal_report_audit_20261014/audit.json')
hardware_mapping = read('work/native_snapshot_full_graph_hw_v2_20261014/group_audit/provenance.json')
assert hardware_clock['status'] == 'hardware_clock_metadata_reextracted_and_matched_to_image'
assert hardware_terminal['status'] == 'successful_link_with_failed_requested_setup_timing'
assert hardware_mapping['status'] == 'hardware_xclbin_pointer_mapping_evidence_archived'
assert hardware_clock['xclbin_sha256'] == hardware_terminal['xclbin_sha256'] == hardware_mapping['result']['xclbin_sha256']
assert hardware_clock['tool_reported_achieved_mhz'] < hardware_clock['requested_mhz']
assert hardware_terminal['design_timing_summary']['wns_ns'] < 0
assert next(h for p,h in hardware_constraints['source_sha256'].items() if p.endswith('.rpt')) in hardware_terminal['reports_sha256'].values()

net_trial_comparison = read('work/rr_supplemental_net_transaction_variant_20261015/three_arm_comparison.json')
net_trial_versions = read('work/rr_supplemental_net_transaction_variant_20261015/version_audit_2.json')
net_trial_mutations = read('work/rr_supplemental_net_transaction_variant_20261015/auditor_mutation_checks/audit.json')
net_trial_compatibility = read('work/rr_supplemental_net_transaction_variant_20261015/mode0_parent_compatibility.json')
assert net_trial_comparison['status'] == 'same_source_supplemental_net_trial_three_arms_audited'
assert net_trial_versions['status'] == 'private_and_published_versions_match_trial_epoch_and_final_checkpoints'
assert net_trial_mutations['status'] == 'pristine_and_ten_consistently_rehashed_net_trial_corruptions_checked'
assert net_trial_compatibility['status'] == 'five_repeat_mode0_net_trial_parent_compatibility_audited'
assert net_trial_mutations['original_outputs_unchanged']

ordinary_comparison = read('work/rr_ordinary_schedule_variant_20261015/three_arm_comparison.json')
ordinary_compatibility = read('work/rr_ordinary_schedule_variant_20261015/parent_compatibility.json')
assert ordinary_comparison['status'] == 'same_source_ordinary_schedule_three_arms_audited'
assert ordinary_compatibility['status'] == 'five_repeat_bulk_schedule_parent_compatibility_audited'
ordinary_corruptions = 0
for index in range(3):
    state = read(f'work/rr_ordinary_schedule_variant_20261015/state_audit_{index}.json')
    mutation = read(f'work/rr_ordinary_schedule_variant_20261015/auditor_mutation_checks_{index}/audit.json')
    assert state['status'] == 'five_repeat_ordinary_schedule_paths_ripups_and_versions_audited'
    assert state['modes']['downstream_bounded']['schedule_mode'] == index
    assert state['modes']['downstream_bounded']['final_resources_and_costs_byte_equivalent']
    assert mutation['status'] == 'pristine_and_nine_consistently_rehashed_schedule_corruptions_checked'
    assert mutation['original_outputs_unchanged'] and len(mutation['cases']) == 10
    for case in mutation['cases']:
        assert case['returncodes']['generic'] == 0
        assert (case['returncodes']['schedule'] == 0) == (case['name'] == 'pristine')
    ordinary_corruptions += len(mutation['cases']) - 1

quality_frontier = read('paper/figures/quality_frontier_manifest.json')
assert quality_frontier['status'] == 'observed_completed_native_quality_frontier_exported'
assert all(hashlib.sha256((root / p).read_bytes()).hexdigest() == h
           for p, h in quality_frontier['source_sha256'].items())
assert len(quality_frontier['two_metric_non_degrading_variants']) == 1

present_result = read('work/rr_present_schedule_variant_20261015/result.json')
present_comparison = read('work/rr_present_schedule_variant_20261015/three_arm_comparison_v2.json')
assert present_comparison['status'] == 'same_source_present_schedule_three_arms_audited'
assert present_result['outcomes']['zero_first_warm_start']['ex5p_architecture_model_checks_pass']

legal_retention = read('work/rr_legal_connection_retention_variant_20261015/result.json')
legal_retention_comparison = read('work/rr_legal_connection_retention_variant_20261015/paired_comparison.json')
assert legal_retention['status'] == 'paired_legal_connection_retention_study_complete_quality_regression_no_adoption'
assert legal_retention_comparison['status'] == 'same_source_legal_connection_retention_pair_audited'
retained_result = legal_retention_comparison['outcomes']['legal_retention']['downstream_bounded']
assert retained_result['repeats_verified'] == 5 and retained_result['counters']['legal']
present_cohort = read('work/rr_present_schedule_development_cohort_v1_20261015/result.json')
assert present_cohort['status'] == 'fixed_present_schedule_development_cohort_complete_joint_quality_failure_no_adoption'
assert not present_cohort['all_development_architecture_model_checks_pass']
alu4_fixed = read('work/rr_present_schedule_development_cohort_v1_20261015/alu4/interim_result.json')
assert alu4_fixed['candidate_native_qor']['critical_path_delay_ns'] > alu4_fixed['candidate_native_qor']['baseline_cpd_ns']
diffeq_fixed = read('work/rr_present_schedule_development_cohort_v1_20261015/diffeq/interim_result.json')
assert diffeq_fixed['status'] == 'diffeq_fixed_configuration_native_state_matching_and_corruption_audited_wirelength_gate_failed'

vpr_build = read('work/vpr_source_bound_rebuild_v2_20261015/build_dependency_audit.json')
vpr_native = read('work/vpr_source_bound_rebuild_v2_20261015/native_compatibility_audit.json')
assert vpr_build['status'] == 'new_frozen_vpr_sources_compiler_dependencies_and_link_inputs_audited'
assert vpr_native['status'] == 'five_repeat_source_bound_vpr_native_baseline_compatibility_audited'
assert vpr_native['numerical_and_canonical_compatibility'] and len(vpr_native['cases']) == 5
assert all(c['historical_metrics_equal'] and c['historical_canonical_artifacts_equal']
           and c['historical_rr_graph_equal'] for c in vpr_native['cases'])
assert vpr_native['historical_metrics'] == dict(wirelength=9664, cpd_ns=9.60037)

vpr_hook_build = read('work/vpr_source_bound_timing_build_20261015/manifest.json')
vpr_hook_native = read('work/vpr_source_bound_timing_build_20261015/native_compatibility_audit.json')
vpr_hook = read('work/vpr_source_bound_timing_build_20261015/timing_hook_compatibility/audit.json')
assert set(vpr_hook_build['post_patch_source_sha256']) == {'source_vtr/vpr/src/base/vpr_api.cpp'}
assert vpr_hook_native['numerical_and_canonical_compatibility'] and len(vpr_hook_native['cases']) == 5
assert vpr_hook['status'] == 'source_bound_vpr_timing_hook_outputs_compared_to_archived_epochs'
assert vpr_hook['all_epoch_outputs_byte_equivalent']
assert all(c['byte_equivalent'] for c in vpr_hook['epochs'])

vpr_setup = read('work/vpr_source_bound_net_setup_observation_20261015/setup_observation_audit.json')
vpr_setup_native = read('work/vpr_source_bound_net_setup_observation_20261015/native_compatibility_audit.json')
vpr_setup_build = read('work/vpr_source_bound_net_setup_observation_20261015/manifest.json')
assert vpr_setup['status'] == 'five_repeat_canonical_compatible_native_setup_observations_audited'
assert vpr_setup['repeats'] == 5 and vpr_setup_native['numerical_and_canonical_compatibility']
assert set(vpr_setup_build['post_patch_source_sha256']) == {'source_vtr/vpr/src/route/route_net.cpp'}
assert vpr_setup['totals']['setup_calls'] == sum(vpr_setup['totals'][k] for k in
    ('whole_reset_calls','partial_prune_calls','fully_pruned_calls'))

local_guard_local_outcomes = read('work/rr_local_delay_feedback_variant_20261014/local_outcome_profile.json')
assert local_guard_local_outcomes['status'] == 'executed_guarded_supplemental_local_delay_outcomes_profiled'

local_guard_comparison = read('work/rr_local_delay_feedback_variant_20261014/three_arm_comparison.json')
local_guard_profile = read('work/rr_local_delay_feedback_variant_20261014/guarded_crossing_profile.json')
local_guard_versions = read('work/rr_local_delay_feedback_variant_20261014/version_audit_2.json')
local_guard_mutations = read('work/rr_local_delay_feedback_variant_20261014/auditor_mutation_checks/audit.json')
local_guard_parent_zero = read('work/rr_local_delay_feedback_variant_20261014/parent_compatibility_0.json')
local_guard_parent_on = read('work/rr_local_delay_feedback_variant_20261014/parent_compatibility_1.json')
assert local_guard_comparison['status'] == 'same_source_local_delay_feedback_three_arms_audited'
assert local_guard_profile['status'] == 'audited_guarded_trajectory_crossings_profiled'
assert local_guard_versions['status'] == 'serial_version_history_matches_epoch_and_final_checkpoints'
assert local_guard_mutations['status'] == 'pristine_and_four_guarded_pending_feedback_corruptions_checked'
assert local_guard_parent_zero['status'] == local_guard_parent_on['status'] == 'five_repeat_disabled_local_delay_guard_compatibility_audited'
local_guard_result = local_guard_comparison['outcomes']['guarded']['downstream_bounded']
assert local_guard_result['repeats_verified'] == 5 and local_guard_result['counters']['legal']

local_guard_components = read('work/rr_local_delay_feedback_variant_20261014/component_progress.json')
local_guard_design = read('experiments/local_delay_guarded_feedback_protocol_v1.json')
assert local_guard_components['status'] == 'guard_component_and_fully_instrumented_semantic_checks_passed'

critical_pair = read('work/rr_critical_feedback_variant_20261014/feedback_comparison.json')
critical_trigger = read('work/rr_critical_feedback_variant_20261014/trigger_delay_profile.json')
critical_version_candidate = read('work/rr_critical_feedback_variant_20261014/version_audit_1.json')
assert critical_pair['status'] == 'same_source_critical_feedback_pair_audited'
assert critical_trigger['status'] == 'observed_supplemental_feedback_delay_changes_profiled'
assert critical_version_candidate['status'] == 'serial_version_history_matches_epoch_and_final_checkpoints'
critical_candidate = critical_pair['outcomes']['candidate']['downstream_bounded']
assert critical_candidate['repeats_verified'] == 5 and critical_candidate['counters']['legal']
critical_trigger_mode = critical_trigger['modes']['downstream_bounded']

cross = read('work/native_snapshot_sharded_native_v1_20261014/cross_die/independent_audit.json')
joint = read('work/native_snapshot_sharded_joint_xrt_v3_20261014/independent_audit.json')
smoke = read('work/native_snapshot_sharded_native_xrt_v2_20261014/smoke/independent_audit.json')
smoke_commit = read('work/native_snapshot_sharded_native_xrt_v2_20261014/smoke/artifacts/commit/independent_audit.json')
qor = read('experiments/wide_timing_cohort_audit_20261013.json')
geometry = read('work/rr_geometry_zero_supervision_20261014/comparison.json')
delay = read('work/rr_native_delay_error_cohort_v2_20261014.json')
entry_audit = read('work/rr_upstream_cost_variant_20261014/independent_audit.json')
entry = entry_audit['experiments'][0]['modes']['downstream_bounded']
stop_audit = read('work/rr_upstream_target_stop_variant_20261014/independent_audit.json')
stop = stop_audit['experiments'][0]['modes']['downstream_bounded']
comparison = read('work/rr_upstream_target_stop_variant_20261014/comparison_queue.json')
precision_audit = read('work/rr_cost_precision_variant_20261014/independent_audit.json')
precision = precision_audit['experiments'][0]['modes']
precision_control = read('work/rr_cost_precision_coarse_control_20261014/precision_comparison.json')
order_audit = read('work/rr_local_task_order_variant_20261014/independent_audit.json')
order = order_audit['experiments'][0]['modes']['downstream_bounded']
order_control = read('work/rr_local_task_order_preserve_control_20261014/task_order_comparison.json')
cleanup_control = read('work/rr_wide_cleanup_disabled_control_20261014/cleanup_comparison.json')
cleanup = cleanup_control['outcomes']['cleanup']['downstream_bounded']
cleanup_disabled = cleanup_control['outcomes']['disabled']['downstream_bounded']
seed_control = read('work/rr_tree_seed_zero_variant_20261014/tree_seed_comparison.json')
seed_zero = seed_control['outcomes']['zero']['downstream_bounded']
seed_midpoint_control = read('work/rr_tree_seed_midpoint_variant_20261014/tree_seed_midpoint_comparison.json')
seed_midpoint = seed_midpoint_control['outcomes']['midpoint']['downstream_bounded']
span_control = read('work/rr_main_span_cost_variant_20261014/span_price_comparison.json')
span = span_control['outcomes']['priced']['downstream_bounded']
span_compatibility = read('work/rr_main_span_cost_variant_20261014/disabled_extension_compatibility.json')
trace_zero = read('work/rr_attachment_trace_variant_20261014/attachment_audit_0.json')
trace_compatible = read('work/rr_attachment_trace_variant_20261014/compatibility_0.json')
trace_feedback = read('work/rr_attachment_trace_variant_20261014/feedback_profile_0.json')
trace_negative = read('work/rr_attachment_trace_variant_20261014/auditor_mutation_checks/audit.json')
trace_midpoint = read('work/rr_attachment_trace_variant_20261014/attachment_audit_1.json')
trace_midpoint_compatible = read('work/rr_attachment_trace_variant_20261014/compatibility_1.json')
trace_midpoint_feedback = read('work/rr_attachment_trace_variant_20261014/feedback_profile_1.json')
critical_component = read('work/rr_critical_feedback_variant_20261014/component_audit.json')
critical_protocol = read('work/rr_critical_feedback_variant_20261014/protocol.json')
critical_disabled = read('work/rr_critical_feedback_variant_20261014/disabled_compatibility.json')
critical_pending = read('work/rr_critical_feedback_variant_20261014/feedback_audit_0.json')
critical_versions = read('work/rr_critical_feedback_variant_20261014/version_audit_0.json')
critical_mutations = read('work/rr_critical_feedback_variant_20261014/auditor_mutation_checks/audit.json')
# The builder freezes the mutable research plan before evidence export.
plan = read('paper/research_plan_snapshot.json')
assert all(x['status'] == 'passed' for x in (cross, joint, smoke))
assert smoke_commit['status'] == 'passed' and smoke_commit['all_net_trees_checked'] == 341
assert geometry['status'] == 'five_repeats_geometry_zero_has_identical_routes_and_counters'
assert delay['status'] == 'measured_inputs_verified'
for case in delay['cases']:
    verification = read(case['independent_xml_audit'])
    assert verification['status'] == 'passed'
    assert verification['profile_sha256'] == case['profile_sha256']
assert entry['status'] == 'passed' and entry['repeats_verified'] == 5
assert stop['status'] == 'passed' and stop['repeats_verified'] == 5
assert comparison['status'] == 'five_repeat_path_authority_equivalence_audited'
assert len(comparison['equal_artifacts']) == 30
assert all(precision[mode]['status'] == 'passed' and precision[mode]['repeats_verified'] == 5
           for mode in ('flat','downstream_bounded'))
assert precision_control['status'] == 'same_source_precision_pair_audited'
assert order['status'] == 'passed' and order['repeats_verified'] == 5
assert order_control['status'] == 'same_source_task_order_pair_audited'
assert cleanup_control['status'] == 'same_source_cleanup_pair_audited'
assert all(x['status']=='passed' and x['repeats_verified']==5 for x in (cleanup,cleanup_disabled))
assert cleanup['native_qor']['critical_path_delay_ns']==cleanup_disabled['native_qor']['critical_path_delay_ns']
assert seed_control['status']=='same_source_tree_seed_weight_pair_audited'
assert seed_zero['status']=='passed' and seed_zero['repeats_verified']==5
assert seed_midpoint_control['status']=='same_source_tree_seed_midpoint_pair_audited'
assert seed_midpoint['status']=='passed' and seed_midpoint['repeats_verified']==5
assert span_control['status']=='same_source_channel_span_price_pair_audited'
assert span['status']=='passed' and span['repeats_verified']==5
assert span_compatibility['status']=='five_repeat_disabled_span_extension_compatibility_audited'
assert trace_zero['status']=='five_repeat_attachment_replay_audited'
assert trace_compatible['status']=='five_repeat_attachment_trace_compatibility_audited'
assert trace_feedback['status']=='actual_attachment_and_final_feedback_joined'
assert trace_negative['status']=='pristine_and_six_refreshed_hash_corruptions_checked'
assert trace_negative['original_outputs_unchanged']
assert all(case['root_checks_passed'] for case in trace_negative['cases'])
assert trace_negative['cases'][0]['replay_returncode']==0
assert all(case['replay_returncode']!=0 for case in trace_negative['cases'][1:])
assert trace_midpoint['status']=='five_repeat_attachment_replay_audited'
assert trace_midpoint_compatible['status']=='five_repeat_attachment_trace_compatibility_audited'
assert trace_midpoint_feedback['status']=='actual_attachment_and_final_feedback_joined'
assert critical_component['status']=='component_and_fully_instrumented_controller_checks_passed'
assert critical_protocol['status']=='frozen_before_execution'
assert critical_disabled['status']=='five_repeat_disabled_critical_feedback_compatibility_audited'
assert critical_pending['status']=='five_repeat_critical_feedback_pending_and_owner_replay_audited'
assert critical_versions['status']=='serial_version_history_matches_epoch_and_final_checkpoints'
assert critical_mutations['status']=='pristine_and_four_pending_feedback_corruptions_checked'
midpoint_example=next(row for row in trace_midpoint_feedback['final_capped_with_last_acceptance_below_cap'] if row['task_id']==934)
assert midpoint_example['attachment']==midpoint_example['source'] and midpoint_example['prefix_delay_q']==0
lines = ['% Generated by tools/export_research_draft_evidence.py; do not edit.']
numbers = dict(CrossExpanded=cross['result']['expanded'], CrossObservations=cross['result']['observations'],
               CrossCost=cross['result']['cost'], JointCalls=joint['actual_cu_calls'],
               SmokeExpanded=smoke['result']['expanded'], SmokeUpload=smoke['result']['verified_upload_bytes'],
               DelayConnections=delay['connections'], EntryWL=entry['native_qor']['total_wirelength'],
               EntryCPD=entry['native_qor']['critical_path_delay_ns'],
               EntryExpanded=entry['counters']['expanded'])
numbers.update(StopExpanded=stop['counters']['expanded'],
               StopUpstreamReduction=f"{100*(1-stop['counters']['upstream_expanded']/entry['counters']['upstream_expanded']):.2f}",
               StopTotalReduction=f"{100*(1-stop['counters']['expanded']/entry['counters']['expanded']):.2f}")
for name, mode in (('FineFlat','flat'),('FineDown','downstream_bounded')):
    numbers[name+'WL'] = precision[mode]['native_qor']['total_wirelength']
    numbers[name+'CPD'] = precision[mode]['native_qor']['critical_path_delay_ns']
    numbers[name+'Iterations'] = precision[mode]['counters']['iterations']
numbers.update(LocalOrderWL=order['native_qor']['total_wirelength'],
               LocalOrderCPD=order['native_qor']['critical_path_delay_ns'],
               LocalOrderIterations=order['counters']['iterations'])
numbers.update(CleanupWL=cleanup['native_qor']['total_wirelength'],
               CleanupBeforeWL=cleanup_disabled['native_qor']['total_wirelength'],
               CleanupCPD=cleanup['native_qor']['critical_path_delay_ns'],
               CleanupAccepted=cleanup['counters']['cleanup_accepted_nets'],
               CleanupWireReduction=cleanup_disabled['native_qor']['total_wirelength']-cleanup['native_qor']['total_wirelength'],
               CleanupExpandedIncrease=f"{100*(cleanup['counters']['expanded']/cleanup_disabled['counters']['expanded']-1):.2f}",
               CleanupWLDelta=f"{cleanup['native_qor']['wirelength_delta_percent']:.2f}")
numbers.update(ZeroSeedWL=seed_zero['native_qor']['total_wirelength'],
               ZeroSeedCPD=seed_zero['native_qor']['critical_path_delay_ns'],
               ZeroSeedWLDelta=f"{seed_zero['native_qor']['wirelength_delta_percent']:.2f}",
               ZeroSeedCPDDelta=f"{seed_zero['native_qor']['cpd_delta_percent']:.2f}")
numbers.update(MidSeedWL=seed_midpoint['native_qor']['total_wirelength'],
               MidSeedCPD=seed_midpoint['native_qor']['critical_path_delay_ns'],
               MidSeedWLDelta=f"{seed_midpoint['native_qor']['wirelength_delta_percent']:.2f}",
               MidSeedCPDDelta=f"{seed_midpoint['native_qor']['cpd_delta_percent']:.2f}")
numbers.update(SpanWL=span['native_qor']['total_wirelength'],SpanCPD=span['native_qor']['critical_path_delay_ns'],
               SpanWLReduction=span_control['outcomes']['control']['downstream_bounded']['native_qor']['total_wirelength']-span['native_qor']['total_wirelength'],
               SpanCompatibleArtifacts=span_compatibility['equal_common_artifacts'])
numbers.update(TraceAccepted=trace_zero['modes']['downstream_bounded']['accepted_rows'],
               TraceCompatibleArtifacts=trace_compatible['equal_common_artifacts'],
               TraceFinalCapped=trace_feedback['final_capped'],
               TraceBelowFinalCap=len(trace_feedback['final_capped_with_last_acceptance_below_cap']))
numbers['TraceCorruptions']=len(trace_negative['cases'])-1
numbers.update(TraceMidAccepted=trace_midpoint['modes']['downstream_bounded']['accepted_rows'],
               TraceMidCapped=trace_midpoint_feedback['final_capped'],
               TraceMidBelowCap=len(trace_midpoint_feedback['final_capped_with_last_acceptance_below_cap']),
               TraceMidExampleBranch=midpoint_example['branch_delay_q'])
numbers.update(FeedbackWL=critical_candidate['native_qor']['total_wirelength'],
               FeedbackCPD=critical_candidate['native_qor']['critical_path_delay_ns'],
               FeedbackSupplemental=critical_trigger_mode['supplemental_events'],
               FeedbackUnchanged=critical_trigger_mode['no_local_path_increase'])
numbers.update(HardwareNoInputDelay=hardware_constraints['constraint_counts']['no_input_delay'],
               HardwareNoOutputDelay=hardware_constraints['constraint_counts']['no_output_delay'])
numbers.update(HardwareRequestedMHz=hardware_clock['requested_mhz'],
               HardwareReportedMHz=hardware_clock['tool_reported_achieved_mhz'],
               HardwareDataMHz=hardware_clock['data_clock_topology_mhz'],
               HardwareWNS=hardware_terminal['design_timing_summary']['wns_ns'],
               HardwareFailingEndpoints=hardware_terminal['design_timing_summary']['failing_setup_endpoints'],
               HardwarePointers=hardware_mapping['result']['pointer_arguments'])
numbers.update(CommitUnbankedLUT=commit_hls_layouts['resource_changes']['LUT']['unbanked'],
               CommitBankedLUT=commit_hls_layouts['resource_changes']['LUT']['banked'],
               CommitLUTIncrease=f"{commit_hls_layouts['resource_changes']['LUT']['delta_percent']:.1f}",
               CommitFFIncrease=f"{commit_hls_layouts['resource_changes']['FF']['delta_percent']:.1f}")
numbers.update(LocalGuardWL=local_guard_result['native_qor']['total_wirelength'],
               LocalGuardCPD=local_guard_result['native_qor']['critical_path_delay_ns'],
               LocalGuardWLDelta=f"{local_guard_result['native_qor']['wirelength_delta_percent']:.2f}",
               LocalGuardCPDDelta=f"{local_guard_result['native_qor']['cpd_delta_percent']:.2f}",
               LocalGuardSupplemental=local_guard_profile['modes']['downstream_bounded']['actual_supplemental_events'],
               LocalGuardCompatibleArtifacts=local_guard_parent_on['equal_common_artifacts'])
guarded_events = local_guard_local_outcomes['modes']['downstream_bounded']['events']
slower_guarded = [c for e in guarded_events for c in e['connections'] if c['delta_ps'] > 0]
numbers.update(LocalGuardSlowerEvents=sum(any(c['delta_ps']>0 for c in e['connections']) for e in guarded_events),
               LocalGuardSlowerConnections=len(slower_guarded),
               LocalGuardMaxIncrease=max(c['delta_ps'] for c in slower_guarded))
for label, macro in [('parent','NetTrialParent'),('staged','NetTrialStaged'),('guarded','NetTrialGuarded')]:
    result = net_trial_comparison['outcomes'][label]['downstream_bounded']
    assert result['repeats_verified'] == 5 and result['counters']['legal']
    numbers[macro+'WL'] = result['native_qor']['total_wirelength']
    numbers[macro+'CPD'] = result['native_qor']['critical_path_delay_ns']
net_trial_version = net_trial_versions['modes']['downstream_bounded']
numbers.update(NetTrialQueries=net_trial_version['private_queries'],
               NetTrialHashFields=net_trial_version['private_resource_hash_fields_matched'],
               NetTrialPublished=net_trial_version['published_net_trials'],
               NetTrialRejected=net_trial_version['rejected_net_trials'],
               NetTrialDiscardedVersions=sum(net_trial_version['discarded_private_version_increments'].values()),
               NetTrialMutations=len(net_trial_mutations['cases'])-1,
               NetTrialCompatible=net_trial_compatibility['equal_common_artifacts'])
for label, macro in [('bulk','OrdinaryBulk'),('dispatch','OrdinaryDispatch'),('serial','OrdinarySerial')]:
    result = ordinary_comparison['outcomes'][label]['downstream_bounded']
    assert result['repeats_verified'] == 5 and result['counters']['legal']
    numbers[macro+'WL'] = result['native_qor']['total_wirelength']
    numbers[macro+'CPD'] = result['native_qor']['critical_path_delay_ns']
numbers.update(OrdinaryCorruptions=ordinary_corruptions,
               OrdinaryCompatible=ordinary_compatibility['equal_common_artifacts'])
numbers.update(QualityFrontierEntries=len(quality_frontier['rows']),
               QualityFrontierPoints=len(quality_frontier['unique_points']))
numbers.update(VPRFrozenFiles=vpr_build['frozen_source_files_verified'],
               VPRCompiledUnits=len(vpr_build['translation_units']),
               VPRDependencyInputs=len(vpr_build['dependency_sha256']),
               VPRNativeRepeats=len(vpr_native['cases']),
               VPRBaselineWL=vpr_native['historical_metrics']['wirelength'],
               VPRBaselineCPD=vpr_native['historical_metrics']['cpd_ns'])
numbers.update(VPRHookNativeRepeats=len(vpr_hook_native['cases']),
               VPRHookEpochs=len(vpr_hook['epochs']),
               VPRHookRows=sum(c['rows'] for c in vpr_hook['epochs']))
numbers.update(VPRSetupCalls=vpr_setup['totals']['setup_calls'],
               VPRSetupEpochs=len(vpr_setup['per_iteration']),
               VPRWholeReset=vpr_setup['totals']['whole_reset_calls'],
               VPRPartialPrune=vpr_setup['totals']['partial_prune_calls'],
               VPRFullPrune=vpr_setup['totals']['fully_pruned_calls'],
               VPRRetainedFlags=vpr_setup['totals']['retained_sink_flag_occurrences'])
for label, macro in [('legacy','PresentLegacy'),('slow_growth','PresentSlow'),('zero_first_warm_start','PresentWarm')]:
    result = present_result['outcomes'][label]
    compared = present_comparison['outcomes'][label]['downstream_bounded']
    assert compared['repeats_verified'] == 5 and compared['counters']['legal']
    assert result['native_qor'] == compared['native_qor']
    numbers[macro+'WL'] = result['native_qor']['total_wirelength']
    numbers[macro+'CPD'] = result['native_qor']['critical_path_delay_ns']
    numbers[macro+'Crossings'] = result['final_net_crossing_edges']
    numbers[macro+'Epochs'] = result['iterations']
numbers.update(PresentBaselineCrossings=present_result['outcomes']['zero_first_warm_start']['baseline_model_crossings']['net_crossing_edges'],
               PresentWarmExpanded=present_result['outcomes']['zero_first_warm_start']['expanded'],
               PresentWarmExpansionRatio=round(present_result['outcomes']['zero_first_warm_start']['expanded']/present_result['outcomes']['legacy']['expanded'],2))
numbers.update(LegalRetainedOccurrences=legal_retention['retention_state']['retained_connection_occurrences'],
               LegalRetentionWL=retained_result['native_qor']['total_wirelength'],
               LegalRetentionCPD=retained_result['native_qor']['critical_path_delay_ns'],
               LegalRetentionExpanded=retained_result['counters']['expanded'],
               LegalRetentionEpochs=retained_result['counters']['iterations'],
               FixedDiffeqWL=diffeq_fixed['native_qor']['total_wirelength'],
               FixedDiffeqBaselineWL=diffeq_fixed['native_qor']['baseline_wirelength'],
               FixedDiffeqCPD=diffeq_fixed['native_qor']['critical_path_delay_ns'],
               FixedDiffeqBaselineCPD=diffeq_fixed['native_qor']['baseline_cpd_ns'])
numbers.update(FixedAluWL=alu4_fixed['candidate_native_qor']['total_wirelength'],
               FixedAluCPD=alu4_fixed['candidate_native_qor']['critical_path_delay_ns'],
               FixedAluBaselineCPD=alu4_fixed['candidate_native_qor']['baseline_cpd_ns'])
numbers.update(PersistentFreshMedian=round(persistent_pairs['median_fresh_seconds'],2),
               PersistentMedian=round(persistent_pairs['median_persistent_seconds'],2),
               PersistentPairedRatio=round(persistent_pairs_audit['median_paired_ratio'],2),
               PersistentRatioMin=round(persistent_pairs_audit['range_ratio'][0],2),
               PersistentRatioMax=round(persistent_pairs_audit['range_ratio'][1],2))
numbers.update(CriticalityShiftWL=criticality_pair['outcomes']['shift']['native_qor']['total_wirelength'],
               CriticalityShiftCPD=criticality_pair['outcomes']['shift']['native_qor']['critical_path_delay_ns'],
               CriticalityShiftCrossings=criticality_pair['outcomes']['shift']['model_crossings'],
               CriticalityShiftEpochs=criticality_pair['outcomes']['shift']['counters']['iterations'],
               CriticalityShiftExpanded=criticality_pair['outcomes']['shift']['counters']['expanded'])
numbers.update(BankedSnapshotWNS=banked_snapshot['design_timing_summary']['wns_ns'],
               BankedSnapshotTNS=banked_snapshot['design_timing_summary']['tns_ns'],
               BankedSnapshotFailingEndpoints=banked_snapshot['design_timing_summary']['failing_setup_endpoints'],
               BankedSnapshotWorstData=banked_snapshot['worst_displayed_path']['data_delay_ns'],
               BankedSnapshotWorstRoute=banked_snapshot['worst_displayed_path']['route_delay_ns'])
numbers.update(BankedReportedMHz=banked_clock['tool_reported_achieved_mhz'],
               BankedDataMHz=banked_clock['data_clock_topology_mhz'],
               BankedPointers=banked_groups['pointer_arguments'],
               BankedLUT=int(banked_reports['resources']['lut']),
               BankedFF=int(banked_reports['resources']['ff']),
               BankedBRAM=int(banked_reports['resources']['bram_tiles']),
               BankedURAM=int(banked_reports['resources']['uram']),
               BankedDSP=int(banked_reports['resources']['dsp']),
               BankedDRCWarnings=banked_reports['drc_severity_counts']['Warning'],
               BankedDRCAdvisories=banked_reports['drc_severity_counts']['Advisory'],
               BankedNoInputDelay=banked_reports['constraint_counts']['no_input_delay'],
               BankedNoOutputDelay=banked_reports['constraint_counts']['no_output_delay'])
numbers.update(StaticSourceRemoteReads=static_placement['outcomes']['0']['remote_shadow_read_entries'],
               StaticDestinationRemoteReads=static_placement['outcomes']['2']['remote_shadow_read_entries'],
               StaticRemoteReduction=round(static_placement['remote_read_entry_reduction_percent'],2),
               StaticMovedOccurrences=static_placement['outcomes']['2']['receipts_per_repeat']['moved_task_occurrences'],
               StaticLogicalMovedBytes=static_placement['outcomes']['2']['receipts_per_repeat']['logical_moved_envelope_bytes'],
               StaticPlacementWL=static_placement['outcomes']['2']['native_qor']['total_wirelength'],
               StaticPlacementCPD=static_placement['outcomes']['2']['native_qor']['critical_path_delay_ns'])
numbers.update(InitialNativeWL=initial_pair['outcomes']['native']['native_qor']['total_wirelength'],
               InitialNativeCPD=initial_pair['outcomes']['native']['native_qor']['critical_path_delay_ns'],
               InitialNativeCrossings=initial_pair['outcomes']['native']['model_crossings'],
               InitialObservedTasks=initial_join['tasks'],InitialQMin=initial_join['initial_q_min'],
               InitialQMax=initial_join['initial_q_max'],InitialQDistinct=initial_join['initial_q_distinct'])
numbers.update(ReceivedNativeSeeds=receiver_native['total_received_seed_rows'],
               ReceivedNativeRequests=receiver_native['total_received_requests'],
               CreditNativeTasks=credit_native['outcomes']['entry_credit']['credit_per_repeat']['tickets'],
               CreditEntryStalls=credit_native['outcomes']['entry_credit']['credit_per_repeat']['events']['backpressure'],
               CreditByteStalls=credit_native['outcomes']['byte_credit']['credit_per_repeat']['events']['backpressure'],
               CreditByteLimit=credit_protocol['arms']['byte_credit']['bytes'])
numbers.update(AdaptiveNativeBackpressure=adaptive_native['outcomes']['adaptive']['per_repeat']['backpressure'],
               AdaptiveNativeRemote=adaptive_native['outcomes']['adaptive']['per_repeat']['remote_read_entries'],
               AdaptiveNativeWindows=adaptive_native['outcomes']['adaptive']['per_repeat']['checked_policy_windows'])
numbers.update(HBMFailingSetup=clock_rows['hbm_aclk']['setup_failing'],
               HBMWorstSlack=clock_rows['hbm_aclk']['wns_ns'],
               KernelFailingSetup=clock_rows['clk_kernel_00_unbuffered_net']['setup_failing'])
for arm, prefix in [('fanout_bulk','FanoutBulk'), ('fanout_serial','FanoutSerial')]:
    numbers[prefix+'WL'] = fanout_terminal['outcomes'][arm]['wirelength']
    numbers[prefix+'CPD'] = fanout_terminal['outcomes'][arm]['cpd_ns']
numbers.update(FullSeedFanoutWL=seed_weight['outcomes']['weight256']['wirelength'],
               FullSeedFanoutCPD=seed_weight['outcomes']['weight256']['cpd_ns'])
numbers.update(APIJournalEntries=api_coverage_first['unique_node_occurrences'],
               APIProposalPhases=api_coverage_first['proposal_phases'],
               APIResourceCalls=api_coverage_first['resource_api_calls'],
               APICostCalls=api_coverage_first['cost_api_calls'])
assert bus_skew_audit['checkpoint_sha256']==banked_reports['checkpoint_sha256']
numbers.update(BusSkewNumericConstraints=bus_skew_audit['numeric_constraints'],
               BusSkewMinimumSlack=bus_skew_audit['minimum_numeric_slack_ns'])
numbers.update(WarmFanoutWL=fanout_present['outcomes']['present2_fanout1']['wirelength'],
               WarmFanoutCPD=fanout_present['outcomes']['present2_fanout1']['cpd_ns'],
               WarmFanoutCrossings=fanout_present['outcomes']['present2_fanout1']['model_crossings'])
numbers.update(APICoveredTotalEntries=api_coverage_terminal['covered_totals']['unique_node_occurrences'],
               APICoveredTotalPhases=api_coverage_terminal['covered_totals']['proposal_phases'],
               APICoveredTotalStale=api_coverage_terminal['covered_totals']['stale_replays'],
               APICoverageMatchedArtifacts=api_coverage_terminal['matched_control_artifacts'],
               FourLayerSourceFiles=four_layer_build['frozen_source_files_verified'],
               FourLayerTranslationUnits=len(four_layer_build['translation_units']))
numbers.update(STARepairBestWL=STA_budget_best['wirelength'],STARepairBestCPD=STA_budget_best['cpd_ns'])
numbers.update(SlackCheckpointWL=slack_first_WL_checkpoint['wirelength'],SlackCheckpointCPD=slack_first_WL_checkpoint['cpd_ns'],SlackCheckpointCrossings=slack_first_WL_checkpoint['crossings'])
numbers.update(SlackExFinalWL=slack_ex5p_final['wirelength'],SlackExFinalCPD=slack_ex5p_final['cpd_ns'],SlackExFinalCrossings=slack_ex5p_final['crossings'],SlackExFinalAccepted=slack_ex5p_final['accepted'],SlackExNativeCalls=slack_ex5p_final['native_calls'])
for case,prefix in [('diffeq','SlackDiffeq'),('alu4','SlackAlu')]:
    row=slack_cohort_cases[case]
    numbers.update({prefix+'WL':row['wirelength'],prefix+'CPD':row['cpd_ns'],prefix+'Crossings':row['crossings'],prefix+'Accepted':row['accepted']})
for case,prefix in [('ex5p','RefreshedEx'),('diffeq','RefreshedDiff'),('alu4','RefreshedAlu')]:
    row=refreshed_cases[case]
    numbers.update({prefix+'WL':row['wirelength'],prefix+'CPD':row['cpd_ns'],prefix+'Crossings':row['crossings'],prefix+'Accepted':row['accepted']})
for row in compound_timing['cases']:
    prefix={'ex5p':'CompoundEx','diffeq':'CompoundDiff','alu4':'CompoundAlu'}[row['case']]
    numbers[prefix+'Seconds']=round(row['full_case_wall_ns']/1e9,1)
for arm,prefix in [('static','TailStatic'),('adaptive','TailAdaptive')]:
    rows=migration_pair['outcomes'][arm]
    numbers[prefix+'Seconds']=round(sum(r['full_run_wall_ns'] for r in rows)/len(rows)/1e9,1)
    numbers[prefix+'Backpressure']=rows[0]['backpressure']
    numbers[prefix+'RemoteReads']=rows[0]['remote_shadow_reads']
numbers.update(LeanStartLUTDelta=-lean_start['resource_delta']['LUT'],LeanStartFFDelta=-lean_start['resource_delta']['FF'],LeanStartDSPDelta=-lean_start['resource_delta']['DSP'])
numbers['AdaptiveRefinementSeconds']=round(adaptive_compound['refinement_wall_ns']/1e9,1)
# Current reserved and optimized CPU evidence is cited explicitly in the prose.
implicit_full = read('work/native_implicit_compound_review_20261017/independent_audit.json')
implicit_strict = read('work/implicit_strict_decision_equivalence_20261017/audit.json')
implicit_timing = read('work/native_implicit_compound_timing_review_20261017/audit.json')
assert implicit_strict['all_equal']
reserved_baselines = read('work/reserved_native_baselines_20261017/independent_audit.json')
reserved_parent_cohort = read('work/reserved_apex2_parent_cohort_review_20261017/audit.json')
assert len(reserved_parent_cohort['cases']) == 5
reserved_first = read('work/reserved_apex2_seed1_refinement_review_20261017/audit.json')
assert reserved_first['checks']['native_legal'] and not reserved_first['joint_quality_pass']
reserved_second = read('work/reserved_apex2_seed2_refinement_review_20261017/audit.json')
assert reserved_second['joint_quality_pass'] and all(reserved_second['checks'].values())
reserved_cohort = read('work/reserved_apex2_five_seed_summary_20261017/audit.json')
assert reserved_cohort['joint_passes'] == 3 and reserved_cohort['legal_routes'] == 5
for reserved_seed in (3, 4, 5):
    read(f'work/reserved_apex2_seed{reserved_seed}_refinement_review_20261017/audit.json')

read('work/lean_start_300MHz_timing_failure_interim_20261017/audit.json')
read('work/lean_start_routed_critical_path_diagnosis_20261017/audit.json')
read('work/traffic_read_buffer_actual_XO_review_20261017/audit.json')
read('work/lean_start_traffic_read_buffer_HLS_20261017/independent_audit.json')
read('work/lean_start_traffic_read_buffer_RTL_20261017/independent_audit.json')

lean_terminal = read('work/lean_start_routed_review_20261017/independent_audit.json')
assert lean_terminal['route']['complete'] and not lean_terminal['checks']['setup']

read('work/traffic_read_buffer_RTL_cycle_comparison_20261017/audit.json')

capacity_coverage = read('work/native_capacity_coverage_20261017/independent_audit.json')
assert len(capacity_coverage['outcomes']) == 6 and sum(r['native_legal'] for r in capacity_coverage['outcomes']) == 2

width_coverage = read('work/native_fixed_placement_width_coverage_20261017/independent_audit.json')
assert len(width_coverage['outcomes']) == 12 and all(r['native_legal'] for r in width_coverage['outcomes'])

width_roundtrip = read('work/width_coverage_roundtrip_20261017/independent_audit.json')
assert len(width_roundtrip['cases']) == 12 and width_roundtrip['total_nodes'] == 40998960 and width_roundtrip['total_edges'] == 77798718

width_costs = read('work/width_coverage_native_costs_20261018/independent_audit.json')
assert len(width_costs['cases']) == 12 and width_costs['total_node_costs_checked'] == 40998960 and width_costs['total_edges_checked'] == 77798718

first_width_parent = read('work/width_coverage_first_parent_evidence_20261018/audit.json')
assert first_width_parent['native_legal'] and first_width_parent['wirelength'] == 17217
assert first_width_parent['cpd_ns'] == 11.3377 and not first_width_parent['research_complete']
second_width_parent = read('work/width_coverage_second_parent_evidence_20261018/audit.json')
assert second_width_parent['native_legal'] and second_width_parent['wirelength'] == 17188
assert second_width_parent['cpd_ns'] == 11.2472 and not second_width_parent['research_complete']
third_width_parent = read('work/width_coverage_third_parent_evidence_20261018/audit.json')
assert third_width_parent['native_legal'] and third_width_parent['wirelength'] == 36609
assert third_width_parent['cpd_ns'] == 12.4724 and not third_width_parent['research_complete']
width_crossings = read('work/width_first_four_crossing_review_20261018/audit.json')
width_crossing_lineage = read('work/width_first_four_crossing_provenance_recheck_20261018/audit.json')
assert width_crossing_lineage['cases'] == 4
assert [(r['baseline_layer_transitions'], r['candidate_layer_transitions']) for r in width_crossings['rows']] == [(1202,1085),(1291,1109),(1778,1765),(1774,1751)]
assert all(r['WL_CPD_crossing_joint_observed'] for r in width_crossings['rows'])
for path, expected in width_crossing_lineage['source_sha256'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path

width_parent_costs = read('work/width_first_four_routing_costs_20261018/audit.json')
assert [r['wall_ms'] for r in width_parent_costs['rows']] == [5149340.0,10671700.0,7002810.0,13937200.0]
helper_RTL = read('work/proposal_generation_split_RTL_20261018/independent_audit.json')
assert helper_RTL['rtl_calls'] == 75 and helper_RTL['rtl_pass'] and helper_RTL['candidate_cycles'] == 314495
helper_XO = read('work/proposal_generation_split_hw_20261018/compiled_XO_review.json')
assert helper_XO['ports'] == 8 and helper_XO['arguments'] == 29 and helper_XO['embedded_source_matches']
helper_compile = read('work/proposal_generation_split_compile_constraints_20261018/audit.json')
assert helper_compile['resource_delta']['LUT'] == 2321 and helper_compile['resource_delta']['FF'] == 2121
helper_final = read('work/proposal_generation_routed_review_20261018/independent_audit.json')
assert helper_final['status'] == 'retained_requested_clock_report_checks_failed'
assert helper_final['design_timing_summary']['wns_ns'] == -0.773
assert helper_final['design_timing_summary']['setup_failing'] == 18317
assert helper_final['route']['complete'] and helper_final['route']['fully_routed'] == 599422
helper_comparison = read('work/proposal_generation_final_timing_comparison_20261018/audit.json')
assert abs(helper_comparison['wns_delta_ns'] - 0.763) < 1e-9
helper_severity = read('work/proposal_generation_DRC_severity_provenance_20261018/audit.json')
publication_helper = read('work/publish_record_split_RTL_20261018/independent_audit.json')
assert publication_helper['rtl_calls'] == 75 and publication_helper['external_ABI_matches_parent']
assert publication_helper['HLS']['estimated_period_ns'] == 4.647
serial_publication = read('work/publish_record_serial_HLS_20261018/independent_RTL_audit.json')
assert serial_publication['rtl_calls'] == 75 and serial_publication['external_ABI_matches_parent']
assert serial_publication['candidate_cycles'] == 323770 and serial_publication['HLS_estimated_period_ns'] == 2.433
serial_final = read('work/publish_record_serial_routed_review_20261018/independent_audit.json')
assert serial_final['design_timing_summary']['wns_ns'] == -2.167
assert serial_final['route']['fully_routed'] == 599070 and serial_final['route']['complete']
serial_comparison = read('work/publish_record_serial_final_timing_comparison_20261018/audit.json')
assert serial_comparison['candidate_minus_parent']['setup_failing'] == 31414
serial_path = read('work/publish_record_serial_final_path_diagnosis_20261018/audit.json')
serial_mapping = read('work/publish_record_serial_final_path_diagnosis_20261018/RTL_mapping.json')
unlink_rtl = read('work/ripup_predecessor_helper_HLS_20261018/independent_RTL_audit.json')
assert unlink_rtl['rtl_calls'] == 75 and unlink_rtl['candidate_cycles'] == 323805
unlink_xo = read('work/ripup_predecessor_helper_hw_20261018/compiled_XO_review.json')
assert unlink_xo['argument_count'] == 29 and unlink_xo['port_count'] == 8
for evidence in [serial_final, serial_comparison, serial_path, serial_mapping, unlink_rtl, unlink_xo]:
    for path, expected in evidence['source_sha256'].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
unlink_final = read('work/ripup_predecessor_helper_routed_review_20261018/independent_audit.json')
assert unlink_final['design_timing_summary']['wns_ns'] == -1.556
assert unlink_final['design_timing_summary']['setup_failing'] == 35905
assert unlink_final['route']['complete'] and unlink_final['route']['fully_routed'] == 604605
unlink_comparison = read('work/ripup_predecessor_final_timing_comparison_20261020/audit.json')
assert abs(unlink_comparison['candidate_minus_parent']['wns_ns'] - 0.611) < 1e-9
scan_rtl = read('work/negotiate_scan_helper_HLS_20261020/independent_RTL_audit.json')
assert scan_rtl['rtl_calls'] == 75 and scan_rtl['external_ABI_matches_parent']
assert scan_rtl['candidate_cycles'] == 324190
assert scan_rtl['HLS_estimated_period_ns'] == 2.433
assert scan_rtl['resources'] == {'BRAM_18K':0, 'DSP':37, 'FF':155436, 'LUT':196069, 'URAM':0}
scan_xo = read('work/negotiate_scan_helper_hw_20261020/compiled_XO_review.json')
assert scan_xo['arguments'] == 29 and scan_xo['ports'] == 8
for evidence in [unlink_final, unlink_comparison, scan_rtl, scan_xo]:
    for path, expected in evidence['source_sha256'].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
local_exchange_summary = read('work/elliptic_local_exchange_20261020/native_summary.json')
assert local_exchange_summary['joint_passes'] == local_exchange_summary['unique_native_candidates'] == 3
assert local_exchange_summary['candidate_native_probe_total_wall_ns'] == 314608113027
local_exchange_repeat = read('work/elliptic_local_exchange_repeats_20261020/audit.json')
assert len(local_exchange_repeat['repeats']) == 5
local_exchange_selection = read('work/elliptic_local_exchange_20261020/automatic_task_selection.json')
assert [v['task'] for v in local_exchange_selection['selected']] == [3006,2926]
apex_exchange_selection = read('work/apex2_seed1_exchange_native_observation_20261020/automatic_selection.json')
assert apex_exchange_selection['selected'][0]['native_delay_increase_ps'] == 464
apex_exchange_failure = read('work/apex2_seed1_local_exchange_20261020/native_queue/task239_forward/independent_native_audit.json')
assert apex_exchange_failure['cpd_ns'] == 11.1897 and not apex_exchange_failure['checks']['CPD']
assert apex_exchange_failure['model_crossings'] == 1597
apex_capped_exchange = read('work/apex2_seed1_dual_cap_crossing_20261020/native_queue/task239_forward/independent_native_audit.json')
assert apex_capped_exchange['model_crossings'] == 1574 and apex_capped_exchange['cpd_ns'] == 11.1897
apex_stage2_exchange = read('work/apex2_seed1_stage2_unboxed_exchange_20261020/native_queue/task1494_forward/independent_native_audit.json')
assert apex_stage2_exchange['cpd_ns'] == 11.1652 and apex_stage2_exchange['model_crossings'] == 1560
apex_latest_exchange = read('work/apex2_seed1_stage3_current_ceiling_20261020/native_queue/task1289_forward/independent_native_audit.json')
assert apex_latest_exchange['checks']['native_legal'] and not apex_latest_exchange['checks']['CPD']
assert (apex_latest_exchange['wirelength'], apex_latest_exchange['cpd_ns'], apex_latest_exchange['model_crossings']) == (18169, 11.0409, 1511)
apex_latest_review = read('work/apex2_seed1_stage3_current_ceiling_20261020/private_acceptance_review.json')
assert not apex_latest_review['final_baseline_pass'] and apex_latest_review['cpd_improvement_ps'] == '0.3000'
apex_joint_root = 'work/apex2_seed1_reverse_sink_wirelength_refinement_20261020/'
apex_joint_chain = read(apex_joint_root + 'independent_audit.json')
assert apex_joint_chain['final_original_baseline_joint_pass']
assert (apex_joint_chain['final_private_state']['wirelength'], apex_joint_chain['final_private_cpd_ns'], apex_joint_chain['final_private_state']['model_crossings']) == (19170, 10.8308, 1452)
apex_joint_policy = read(apex_joint_root + 'policy_audit.json')
assert apex_joint_policy['status'] == 'rounded_budgets_blocker_first_order_and_native_decisions_verified'
apex_joint_wire = read(apex_joint_root + 'wirelength_audit.json')
assert apex_joint_wire['checks']['native_wirelength_checks'] == 2
apex_joint_order = read(apex_joint_root + 'sink_order_audit.json')
assert len(apex_joint_order['orders']) == 2
apex_joint_recheck = read('work/apex2_seed1_final_joint_pass_native_recheck_20261020/compatibility_audit.json')
assert apex_joint_recheck['status'] == 'final_joint_pass_reloaded_identically_with_legacy_and_source_bound_VPR'
assert apex_joint_recheck['timing_CSV_bytes_identical']
apex_prefix_cost = read('work/apex2_rounded_refinement_first_five_cost_20261020/audit.json')
assert apex_prefix_cost['summed_stage_wall_seconds'] == 244.036520204
seed5_frozen = read('work/apex2_seed5_frozen_reverse_wirelength_refinement_20261020/independent_audit.json')
assert seed5_frozen['final_private_cpd_ns'] == 11.2868 and not seed5_frozen['final_original_baseline_joint_pass']
seed5_delay = read('work/apex2_seed5_ranked_delay_objective_20261020/independent_audit.json')
assert seed5_delay['final_private_cpd_ns'] == 11.2247 and not seed5_delay['final_original_baseline_joint_pass']
seed5_closure = read('work/apex2_seed5_critical_capacity_closure_v2_20261020/independent_construction_review.json')
assert (seed5_closure['restored_nets'], seed5_closure['total_nets'], seed5_closure['unique_native_trees'], seed5_closure['generated_arms']) == (789, 856, 1, 3)
assert (seed5_closure['native_wirelength'], seed5_closure['native_cpd_ns']) == (18917, 11.202)
seed5_native = read('work/apex2_seed5_critical_capacity_closure_v2_20261020/native_queue/task621/independent_native_audit.json')
assert all(seed5_native['checks'].values()) and seed5_native['model_crossings'] == seed5_native['baseline_model_crossings'] == 1442
seed6_initial_exchange = read('work/posterior_critical_minimum_blocker_exchange_20261020/native_summary.json')
assert (seed6_initial_exchange['planned_arms'], seed6_initial_exchange['unique_native_candidates'], seed6_initial_exchange['native_joint_passes']) == (7, 2, 0)
seed6_followup = read('work/posterior_seed6_exchange_followup_20261020/native_summary.json')
assert seed6_followup['joint_passes'] == 0 and len(seed6_followup['rows']) == 2
assert all(v['checks']['CPD'] and not v['checks']['wirelength'] for v in seed6_followup['rows'])
seed6_cleanup = read('work/posterior_seed6_bounded_wire_cleanup_20261020/independent_audit.json')
seed6_cleanup_outcome, = seed6_cleanup['outcomes']
assert seed6_cleanup_outcome['joint_baseline_pass'] and seed6_cleanup_outcome['nets_visited'] == seed6_cleanup_outcome['accepted'] == 1
seed6_reload = read('work/posterior_seed6_final_joint_pass_native_recheck_20261020/compatibility_audit.json')
assert (seed6_reload['wirelength'], seed6_reload['cpd_ns'], seed6_reload['modeled_crossings']) == (19228, 11.1417, 1199)
assert (seed6_reload['baseline_wirelength'], seed6_reload['baseline_cpd_ns'], seed6_reload['baseline_modeled_crossings']) == (19306, 11.1843, 1505)
assert seed6_reload['timing_CSV_bytes_identical'] and seed6_reload['connections'] == 3500
for evidence in [seed6_initial_exchange, seed6_followup, seed6_cleanup, seed6_reload]:
    for name, expected in evidence['source_sha256'].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == expected, name

seed5_reload = read('work/apex2_seed5_final_joint_pass_native_recheck_20261020/compatibility_audit.json')
assert seed5_reload['status'] == 'seed5_final_joint_pass_reloaded_identically_legacy_and_source_bound' and seed5_reload['timing_CSV_bytes_identical']
for evidence in [local_exchange_summary,local_exchange_repeat,local_exchange_selection,apex_exchange_selection,apex_exchange_failure,apex_capped_exchange,apex_stage2_exchange,apex_latest_exchange,apex_latest_review,apex_joint_chain,apex_joint_policy,apex_joint_wire,apex_joint_order,apex_joint_recheck,apex_prefix_cost,seed5_frozen,seed5_delay,seed5_closure,seed5_native,seed5_reload]:
    for path,expected in evidence['source_sha256'].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected,path
restore_direct = read('work/elliptic_critical_net_restore_20261020/independent_native_audit.json')
assert len(restore_direct['arms']) == 3 and not any(a['joint_quality_pass'] for a in restore_direct['arms'])
restore_native = read('work/elliptic_capacity_restore_closure_20261020/independent_native_audit.json')
assert all(restore_native['checks'].values())
assert (restore_native['wirelength'],restore_native['baseline_wirelength']) == (42492,43832)
assert restore_native['cpd_ns'] == restore_native['baseline_cpd_ns'] == 10.4205
restore_mixture = read('work/elliptic_capacity_restore_closure_20261020/independent_net_mixture_review.json')
assert restore_mixture['retained_changed_nets'] == 380
restore_cost = read('work/elliptic_capacity_restore_closure_20261020/probe_cost_review.json')
assert restore_cost['measured_total_wall_ns'] == 427627248905
restore_general = read('work/elliptic_capacity_restore_closure_20261020/general_algorithm_review.json')
assert restore_general['exhaustive_checks']['cases'] == 62500
restore_crosscase = read('work/capacity_closure_crosscase_20261020/independent_audit.json')
assert restore_crosscase['joint_passes'] == restore_crosscase['native_legal_count'] == 3
assert [(v['wirelength'],v['baseline_wirelength'],v['cpd_ns'],v['baseline_cpd_ns']) for v in restore_crosscase['cases']] == [(18405,18471,11.4756,11.6347),(44247,44541,12.474,12.474),(42088,42513,9.94173,9.94173)]
for evidence in [restore_direct,restore_native,restore_mixture,restore_cost,restore_general,restore_crosscase]:
    for path,expected in evidence['source_sha256'].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected,path
scan_final = read('work/negotiate_scan_helper_routed_review_20261020/independent_audit.json')
assert scan_final['design_timing_summary']['wns_ns'] == -1.236
assert scan_final['design_timing_summary']['tns_ns'] == -12223.346
assert scan_final['design_timing_summary']['setup_failing'] == 36299
assert scan_final['route']['complete'] and scan_final['route']['fully_routed'] == 611332
lookup_rtl = read('work/insert_lookup_boundary_HLS_20261020/independent_RTL_audit.json')
assert lookup_rtl['rtl_calls'] == 75 and lookup_rtl['external_ABI_matches_parent']
assert (lookup_rtl['candidate_cycles'],lookup_rtl['parent_cycles']) == (324260,324190)
lookup_boundary = read('work/insert_lookup_boundary_HLS_20261020/helper_boundary_review.json')
assert lookup_boundary['helper_completion_output_is_combinational']
lookup_caller = read('work/insert_lookup_boundary_HLS_20261020/caller_register_boundary_review.json')
assert lookup_caller['caller_register_capture_state'] == 6 and lookup_caller['consumer_helper_state'] == 7
for evidence in [scan_final,lookup_rtl,lookup_boundary,lookup_caller]:
    for path,expected in evidence['source_sha256'].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected,path
sixth_width = read('work/width_coverage_sixth_parent_evidence_20261018/audit.json')
assert sixth_width['native_legal'] and sixth_width['joint_observed_nonincrease']
assert (sixth_width['wirelength'], sixth_width['cpd_ns']) == (32562,9.8666)
assert (sixth_width['baseline_layer_transitions'], sixth_width['candidate_layer_transitions']) == (1865,1849)
seventh_width = read('work/width_coverage_seventh_parent_evidence_20261018/audit.json')
assert seventh_width['native_legal'] and seventh_width['joint_observed_nonincrease']
assert (seventh_width['wirelength'], seventh_width['cpd_ns']) == (18000,11.721)
assert (seventh_width['baseline_layer_transitions'], seventh_width['candidate_layer_transitions']) == (1158,991)
seven_width_summary = read('work/width_coverage_first_seven_summary_20261018/audit.json')
assert seven_width_summary['reviewed'] == 7 and seven_width_summary['planned'] == 12
assert len(seven_width_summary['rows']) == 7
for evidence in [seventh_width, seven_width_summary]:
    for path, expected in evidence['source_sha256'].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
eighth_width = read('work/width_coverage_eighth_parent_evidence_20261018/audit.json')
assert eighth_width['native_legal'] and eighth_width['joint_observed_nonincrease']
assert (eighth_width['wirelength'], eighth_width['cpd_ns']) == (17704,11.7007)
assert (eighth_width['baseline_layer_transitions'], eighth_width['candidate_layer_transitions']) == (1201,980)
eight_width_summary = read('work/width_coverage_first_eight_summary_20261019/audit.json')
assert eight_width_summary['reviewed'] == 8 and eight_width_summary['planned'] == 12
assert len(eight_width_summary['rows']) == 8
for evidence in [eighth_width, eight_width_summary]:
    for path, expected in evidence['source_sha256'].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
all_width_summary = read('work/width_coverage_all_twelve_summary_20261020/audit.json')
assert all_width_summary['reviewed'] == 12 and len(all_width_summary['rows']) == 12
assert all_width_summary['joint_observed_nonincrease_count'] == 11
assert all_width_summary['cpd_regression_count'] == 1
for ordinal in ['ninth','tenth','eleventh','twelfth']:
    evidence = read(f'work/width_coverage_{ordinal}_parent_evidence_20261018/audit.json')
    assert evidence['native_legal']
    for path, expected in evidence['source_sha256'].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
assert sum(row['cpd_delta_percent'] > 0 for row in all_width_summary['rows']) == 1
for path, expected in all_width_summary['source_sha256'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
six_width_summary = read('work/width_coverage_first_six_summary_20261018/audit.json')
assert six_width_summary['reviewed'] == 6 and six_width_summary['planned'] == 12
six_width_plot = read('paper/figures/width_first_six_quality.json')
for path, expected in six_width_plot['artifacts_sha256'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
for evidence in [serial_publication, sixth_width, six_width_summary]:
    for path, expected in evidence['source_sha256'].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
for evidence in [helper_final, helper_comparison, helper_severity, publication_helper]:
    for path, expected in evidence['source_sha256'].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
for evidence in [width_parent_costs, helper_RTL, helper_XO, helper_compile]:
    for path, expected in evidence['source_sha256'].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path

width_five_summary = read('work/width_coverage_first_five_summary_20261018/audit.json')
assert width_five_summary['reviewed'] == 5 and width_five_summary['planned'] == 12
width_five_plot = read('paper/figures/width_first_five_quality.json')
for path, expected in width_five_plot['artifacts_sha256'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path

fifth_width_parent = read('work/width_coverage_fifth_parent_evidence_20261018/audit.json')
assert fifth_width_parent['native_legal'] and fifth_width_parent['joint_observed_nonincrease']
assert (fifth_width_parent['wirelength'], fifth_width_parent['cpd_ns']) == (33882,9.87369)
assert (fifth_width_parent['baseline_layer_transitions'], fifth_width_parent['candidate_layer_transitions']) == (1881,1879)
for path, expected in fifth_width_parent['source_sha256'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path

fourth_width_parent = read('work/width_coverage_fourth_parent_evidence_20261018/audit.json')
assert fourth_width_parent['native_legal'] and fourth_width_parent['wirelength'] == 34659
assert fourth_width_parent['cpd_ns'] == 12.4424 and not fourth_width_parent['research_complete']
traffic_terminal = read('work/traffic_read_buffer_routed_review_20261017/independent_audit.json')
assert traffic_terminal['route']['complete'] and not traffic_terminal['checks']['setup']
assert traffic_terminal['design_timing_summary']['wns_ns'] == -1.951
assert not traffic_terminal['adopted'] and not traffic_terminal['board_result']
read('work/traffic_buffer_vs_lean_requested_clock_comparison_20261018/audit.json')
read('work/traffic_buffer_reported_setup_path_diagnosis_20261018/audit.json')
read('work/traffic_buffer_worst_data_net_locality_20261018/audit.json')
scratch_split = read('work/scratch_split_bundle_RTL_20261018/independent_audit.json')
assert scratch_split['rtl_pass'] and scratch_split['rtl_calls'] == 75
assert scratch_split['candidate_cycles'] == 314460 and not scratch_split['adopted']
scratch_split_xo = read('work/scratch_split_bundle_hw_20261018/compiled_XO_review.json')
assert scratch_split_xo['ports'] == 8 and scratch_split_xo['arguments'] == 29

scratch_terminal = read('work/scratch_split_routed_review_20261018/independent_audit.json')
assert scratch_terminal['route']['complete'] and scratch_terminal['route']['routable'] == 597754
assert scratch_terminal['design_timing_summary']['wns_ns'] == -1.536
assert scratch_terminal['design_timing_summary']['setup_failing'] == 31705
assert not scratch_terminal['checks']['setup'] and not scratch_terminal['adopted']
read('work/scratch_split_requested_clock_failure_interim_20261018/audit.json')

hash_pairs = read('work/upstream_hash_five_pair_summary_20261018/audit.json')
assert hash_pairs['runs'] == 10 and hash_pairs['artifact_comparisons'] == 410 and hash_pairs['native_sessions_reviewed'] == 10
assert all(p['candidate_change_percent'] < 0 for p in hash_pairs['pairs'])
for path, expected in hash_pairs['source_sha256'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
hash_plot = read('paper/figures/upstream_hash_native_pairs.json')
for path, expected in hash_plot['artifacts_sha256'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
numbers['HashMedianTimeReduction'] = f"{-hash_pairs['candidate_time_change_percent']['median']:.2f}"
numbers['HashMinimumTimeReduction'] = f"{-hash_pairs['candidate_time_change_percent']['maximum']:.2f}"
numbers['HashMaximumTimeReduction'] = f"{-hash_pairs['candidate_time_change_percent']['minimum']:.2f}"

diffeq_hash_audit = read('work/upstream_hash_crosscase_pairs_20261018/independent_case_audit_diffeq.json')
assert diffeq_hash_audit['reviewed_attempts'] == 10 and diffeq_hash_audit['planned_attempts_total'] == 20
diffeq_hash = diffeq_hash_audit['cases'][0]
assert diffeq_hash['case'] == 'diffeq' and len(diffeq_hash['runs']) == 10
assert sum(len(v['comparisons']) for v in diffeq_hash['runs']) == 390
for path, expected in diffeq_hash_audit['source_sha256'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
numbers['DiffeqHashMedianReduction'] = f"{-diffeq_hash['median_candidate_change_percent']:.2f}"
numbers['DiffeqHashMinimumReduction'] = f"{-max(v['candidate_change_percent'] for v in diffeq_hash['pairs']):.2f}"
numbers['DiffeqHashMaximumReduction'] = f"{-min(v['candidate_change_percent'] for v in diffeq_hash['pairs']):.2f}"

alu_hash_audit = read('work/upstream_hash_crosscase_pairs_20261018/independent_case_audit_alu4.json')
alu_hash, = alu_hash_audit['cases']
assert alu_hash_audit['reviewed_attempts'] == 10 and alu_hash['case'] == 'alu4' and alu_hash['cost_scale'] == 256
assert len(alu_hash['runs']) == 10 and sum(len(v['comparisons']) for v in alu_hash['runs']) == 390
for path, expected in alu_hash_audit['source_sha256'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
numbers['AluHashMedianReduction'] = f"{-alu_hash['median_candidate_change_percent']:.2f}"
numbers['AluHashMinimumReduction'] = f"{-max(v['candidate_change_percent'] for v in alu_hash['pairs']):.2f}"
numbers['AluHashMaximumReduction'] = f"{-min(v['candidate_change_percent'] for v in alu_hash['pairs']):.2f}"
alu_native = read('work/upstream_hash_alu4_first_pair_review_20261018/audit.json')
assert len(alu_native['native_quality']) == 2 and all(v['wirelength'] == 10083 and v['cpd_ns'] == 10.2653 for v in alu_native['native_quality'])
three_hash_summary = read('work/upstream_hash_three_case_summary_20261018/audit.json')
assert three_hash_summary['total_pairs'] == 15 and three_hash_summary['total_runs'] == 30
for path, expected in three_hash_summary['source_sha256'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
three_hash_plot = read('paper/figures/upstream_hash_three_case_pairs.json')
assert three_hash_plot['status'] == 'three_separate_completed_five_pair_CPU_configurations_rendered'
assert [(v['case'], v['scale']) for v in three_hash_plot['cases']] == [('ex5p',1), ('diffeq',256), ('alu4',256)]
for path, expected in {**three_hash_plot['source_sha256'], **three_hash_plot['artifacts_sha256']}.items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path

for name, value in numbers.items():
    lines.append('\\newcommand{\\' + name + '}{' + str(value) + '}')
lines.append(r'\newcommand{\PersistentPairRows}{%')
for index in range(5):
    records = [r for r in persistent_pairs['records'] if r['pair'] == index]
    assert len(records) == 2 and all(r['status'] == 'completed_and_artifacts_audited' for r in records)
    values = {r['transport']:r['outer_elapsed_ns']/1e9 for r in records}
    order = 'F/P' if records[0]['transport']=='fresh' else 'P/F'
    ratio = persistent_pairs['paired_ratios'][index]
    lines.append(f"{index+1} & {order} & {values['fresh']:.2f} & {values['persistent']:.2f} & {ratio:.2f} " + r'\\')
lines.append('}')
lines.append(r'\newcommand{\SBScalingRows}{%')
for row in sb_scaling['baselines']:
    lines.append(f"{row['layers']} & {row['channel_width']} & {row['rr_nodes']} & {row['isolated_nodes']} & {row['native_wirelength']} & {row['native_cpd_ns']} " + r'\\')
lines.append('}')
lines.append(r'\newcommand{\SBPathRows}{%')
for row in sb_paths['cases']:
    case=row['case'];layers=case.split('_')[0].removeprefix('layers');width=case.split('_')[1].removeprefix('cw')
    counts=[str(row['actual_crossing_hops'].get(str(hop),0)) for hop in range(4)]
    lines.append(' & '.join([layers,width]+counts+[str(row['unique_net_cross_edges'])]) + r'\\')
lines.append('}')
lines.append(r'\newcommand{\DevelopmentQoRRows}{%')
for experiment in qor['experiments']:
    name = Path(experiment['case']).name.split('_')[1]
    values = experiment['modes']['downstream_bounded']['native_qor']
    lines.append(f"{name} & {values['baseline_wirelength']} & {values['total_wirelength']} & "
                 f"{values['wirelength_delta_percent']:.2f}\\% & {values['cpd_delta_percent']:.2f}\\% " + r'\\')
lines.append('}')
lines.append(r'\newcommand{\OwnerExchangeRows}{%')
for row in owner_exchange_interpretation['outcomes']:
    arm, owner = row['label'].removeprefix('feedback_').split('_owner')
    lines.append(f"{arm}/{owner} & {row['native_wirelength']} & {row['native_cpd_ns']:.4f} & {row['candidate_crossings']} " + r'\\')
lines.append('}')
lines.append(r'\newcommand{\GateRows}{%')
for gate in plan['gates']:
    status = gate['status'].replace('_', r'\_')
    lines.append(gate['id'] + ' & ' + status + r' & Not complete \\')
lines.append('}')
(out / 'evidence.tex').write_text('\n'.join(lines) + '\n')
sources['paper/evidence.tex'] = hashlib.sha256((out/'evidence.tex').read_bytes()).hexdigest()
(out / 'evidence_manifest.json').write_text(json.dumps(dict(
    status='draft_numbers_exported', source_sha256=sources, numbers=numbers,
    scope='Direct finalized evidence extraction including five audited entry-cost development repeats; no research completion certification',
    research_complete=False, board_result=False), indent=2) + '\n')
print(json.dumps(dict(status='draft_numbers_exported', sources=len(sources), research_complete=False)))
