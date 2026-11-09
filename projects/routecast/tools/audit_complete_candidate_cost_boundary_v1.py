"""Bind historical dependency stages and expose missing complete-run clocks."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/complete_candidate_cost_boundary_v1_2026-10-08';D.mkdir(exist_ok=False)
spec=[
 ('endpoint_and_original_budget',['tools/pre_route_endpoints.py','tools/prepare_mux_connection_budgets.py'],['experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json','experiments/mux_connection_budgets_2026-10-06/w32.json'],[]),
 ('old_timing_and_edge_mapping',['tools/trial_mux_old_full_timing_graph.py','tools/map_mux_full_timing_rr.py'],['experiments/mux_old_full_timing_graph_2026-10-06/w32_timing_graph.json','experiments/mux_full_timing_rr_2026-10-06/w32.json','experiments/mux_allfanin_budgets_2026-10-06/w32_m2.json'],['endpoint_and_original_budget']),
 ('retained_branch_identity_and_serialization',['tools/certify_endpoint_compatible_branch_trim_v1.py','tools/certify_retained_branch_sink_identity_v2.py'],['experiments/retained_branch_native_serialization_v1_2026-10-08/receipt.json'],['endpoint_and_original_budget']),
 ('partial_native_resume',['tools/native_resume_prototype/trial_branch_partial_v8.py'],['experiments/native_resume_branch_partial_v8_2026-10-08/receipt.json'],['retained_branch_identity_and_serialization']),
 ('full_budget_floor_and_replacement_diagnosis',['tools/native_resume_prototype/estimate_branch_budget_target_floors_v1.py','tools/diagnose_branch_budget_single_replacement_v1.py'],['experiments/branch_budget_target_rr_floors_w32_m2_2026-10-08/receipt.json','experiments/branch_budget_single_replacement_v1_2026-10-08/diagnosis.json'],['partial_native_resume']),
 ('six_occupied_budget_repairs',['tools/trial_budget_occupied_branch_repair_v1.py'],['experiments/budget_occupied_branch_repair_v1_2026-10-08/receipt.json'],['full_budget_floor_and_replacement_diagnosis']),
 ('critical_selection_and_blocking_owners',['tools/trial_critical_branch_constraint_ablation_v1.py'],['experiments/critical_branch_constraint_ablation_v1_2026-10-08/blocking_owners.json'],['six_occupied_budget_repairs','old_timing_and_edge_mapping']),
 ('four_complete_owner_transactions',['tools/trial_critical_owner_transaction_v1.py'],['experiments/critical_owner_transaction_v1_2026-10-08/receipt.json'],['critical_selection_and_blocking_owners']),
 ('complete_three_wire_passes',['tools/profile_complete_wire_search_replay_native_v1.py'],['experiments/complete_wire_search_cost_replay_native_v1_2026-10-08/verification.json'],['four_complete_owner_transactions']),
 ('dynamic_global_guard',['tools/trial_global_guard_wire_contraction_static_multiplicity_v1.py'],['experiments/global_guard_wire_contraction_static_multiplicity_v1_2026-10-08/component_cost_verification.json'],['old_timing_and_edge_mapping','complete_three_wire_passes']),
 ('native_postsync_and_canonical',['tools/trial_global_guard_wire_native_chain_v1.py'],['experiments/global_guard_wire_contraction_v1_2026-10-08/native_quality_verification.json'],['dynamic_global_guard']),
]
bindings={str(Path(__file__)):sha(Path(__file__))};rows=[];seen=set()
for name,tools,artifacts,parents in spec:
 assert set(parents)<=seen;seen.add(name)
 files={}
 for relative in tools+artifacts:
  path=R/relative;assert path.is_file();files[str(path)]=sha(path)
 bindings.update(files)
 rows.append(dict(stage=name,dependencies=parents,files=files,fresh_complete_boundary_wall_seconds=None,clock_status='MISSING_SINGLE_RUN_STAGE_CLOCK',scope='Historical provenance and required state production; inherited artifact is not a timed fresh execution.'))
profile=R/'experiments/complete_wire_search_cost_replay_native_v1_2026-10-08/verification.json';p=json.loads(profile.read_text());assert p['all_complete_cohort_fidelity_and_cost_arithmetic_checks_pass'] and all(sha(f)==h for f,h in p['bindings'].items());bindings.update(p['bindings'])
dynamic=R/'experiments/global_guard_wire_contraction_static_multiplicity_v1_2026-10-08/component_cost_verification.json';g=json.loads(dynamic.read_text());assert g['all1929_semantic_events_and_final_state_equal'] and all(sha(f)==h for f,h in g['bindings'].items());bindings.update(g['bindings'])
assert all(sha(f)==h for f,h in bindings.items())
manifest=dict(bindings=bindings,case=dict(width=32,index=2,complete_connections=1929),stages=rows,observations=dict(three_pass_search_component_seconds=p['elapsed_seconds'],last_pass_dynamic_component_seconds=g['observations'][1]['producer_component_elapsed_seconds']),full_workflow_seconds=None,complete_boundary_measurement_proved=False,can_sum_component_observations_as_full_workflow=False,policy='Fresh clock starts at declared old accepted input plus target layout. Candidate-dependent endpoint/budget/model preparation, retained serialization/resume, six repairs, blocking-owner discovery and all four declared transactions, complete wire searches/global guard, required native/canonical acceptance and audits must be charged or explicitly included in a symmetric initial-cache contract. Frozen states/ceilings are validation references, not free candidate production. Three-pass replay already contains final search; dynamic last-pass observation overlaps it and cannot be added. Do not rerun obsolete exploratory policies as mandatory runtime when final mechanism replaces them, but prove the replacement from declared inputs. Keep all original failures; no result selection or timing reconstruction from file timestamps.')
(D/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
out=dict(manifest_sha256=sha(D/'manifest.json'),verifier_source_sha256=sha(Path(__file__)),all11_historical_stage_files_and_dependency_order_authenticated=True,missing_fresh_stage_clocks=len(rows),full_workflow_seconds=None,scope='Boundary audit only. Authenticated available component clocks are incomplete and overlapping; no end-to-end runtime or gain can be derived. Original failure/equivalence/unseen-family requirements remain.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(out,flush=True)
