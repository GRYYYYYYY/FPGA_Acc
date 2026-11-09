"""Recorded work budgets; separate historical timers never become a paired arm."""
import datetime,json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
cert=R/'experiments/neuron_compiled_final_admission_v1_2026-10-15/verification.json'
label=R/'experiments/neuron_certified_native_metrics_v1_2026-10-15/label_admission.json'
native=R/'experiments/titan23_neuron_native_cold_label_v1_2026-10-14/terminal.json'
workfile=R/'experiments/titan23_neuron_compiled_criticality_pipeline_v1_2026-10-15/model/compiled_primary_work.json'
modelterminal=workfile.parent.parent/'model_terminal.json'
v=json.loads(cert.read_text());a=json.loads(label.read_text());t=json.loads(native.read_text());w=json.loads(workfile.read_text());m=json.loads(modelterminal.read_text())
assert v['all_pass'] and a['label_accepted'] and t['exit_status']==m['exit_status']==0
assert t['seconds']>0 and w==v['native_primitive_work'] and sha(workfile)==v['bindings'][str(workfile)]
assert v['stage_resource_and_terminal_evidence']['model']['terminal']==m
# Preserve the old native launch-time pending label flag. The later admission
# is explicit evidence of post-label semantic closure, not a rewrite of history.
assert not t['label_accepted'] and a['semantic_implementation_extension_after_label']
observed=t['seconds'];scenarios=[]
for fraction in (1,.25,.1,.01):
 budget=observed*fraction
 scenarios.append(dict(native_reference_time_fraction=fraction,hypothetical_estimator_budget_seconds=budget,required_recorded_scanned_arcs_per_second=w['total_scanned_arcs']/budget,required_recorded_settled_nodes_per_second=w['total_settled_nodes']/budget,required_recorded_heap_pushes_per_second=w['total_heap_pushes']/budget))
inputs=[cert,label,native,workfile,modelterminal,Path(__file__)]
result=dict(bindings={str(p):sha(p) for p in inputs},checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),certified_original_connections=v['all_original_connections'],certified_original_full_NET_rounds=2,recorded_work=w,historical_model_process_seconds=m['seconds'],historical_model_resident_seconds=v['compiled_model_timers']['total_paid_resident_seconds'],historical_native_cold_process_seconds=observed,observed_model_process_over_native_process=m['seconds']/observed,paired_comparison=False,continuous_workflow_measured=False,measured_guided_neuron_router_seconds=None,hypothetical_work_budgets=scenarios,necessary_condition='On a matched continuous trial: T_import + T_estimation + T_feedback + T_guided_exact_router + T_required_validation + T_other < T_cold_arm_total, with shared stages and amortization boundary frozen consistently.',interpretation='The recorded complete allNET estimator alone costs much more than the separate historical native cold observation. Even an estimator budget equal to that whole native observation leaves no budget for feedback or guided routing. Hardware replay of unchanged68.4billion scan events would need about547million scans/second merely to fit that optimistic125second budget. This is arithmetic of recorded counts and a hypothetical budget, not hardware throughput, physical memory traffic or a paired no-gain theorem.',requirements_before_benefit_claim=['Matched continuous complete cold/guided arms on identical original inputs and fixed seeds/settings.','Freeze conversion/graph import, snapshot/price maintenance, serialization/feedback, required validation and final exact-router boundaries; state cold versus amortized costs explicitly.','Record actual incremental changed-demand workloads, search work, prediction quality and final routing/QoR; unchanged-result transactions are not valid skip certificates.','For hardware, measure the actual wide-arithmetic frontier/queue and state bandwidth, resource capacity and clock; no one-arc-per-cycle assumption.'],scope='Full original compiled baseline work counts and separately certified native cold timer. No new model, parameter selection, unseen-family, native-guided QoR, throughput or end-to-end gain result. Factors2/4 may have different work and require their own measurements.')
out=R/'experiments/neuron_recorded_work_budget_v1_2026-10-15';out.mkdir();(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(observed_model_seconds=m['seconds'],observed_native_seconds=observed,unpaired_observation_ratio=result['observed_model_process_over_native_process'],scan_events=w['total_scanned_arcs'],optimistic_budget_required_scans_per_second=scenarios[0]['required_recorded_scanned_arcs_per_second'],matched_workflow_measured=False),indent=2))
