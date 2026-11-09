"""Terminal-only work/cost/quality accounting; never relaxes original gates."""
import json,hashlib
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prospective_external_family_bound_group_refinement_v1_2026-10-20';Z=E/'prospective_external_family_sequential_group_refinement_v1_2026-10-20';C=E/'bound_group_refinement_launch_chain_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 chain=read(C/'state.json');assert chain['status']=='ALL_TRIAL_AND_EVALUATION_STAGES_TERMINAL' and chain['exit_status']==0
 terminal=read(D/'terminal.json');assert len(terminal['rows'])==3 and all(q['exit_status']==0 for q in terminal['rows']);quality=read(D/'quality_summary_v1.json');metrics=read(D/'independent_metrics_verification_v1.json');bindings={str(Path(__file__)):sha(__file__)}
 for p in [C/'state.json',D/'protocol.json',D/'terminal.json',D/'quality_summary_v1.json',D/'independent_metrics_verification_v1.json']:
  data=read(p);assert all(sha(k)==h for k,h in data.get('bindings',{}).items());bindings[str(p)]=sha(p)
 rows=[];group_total=checkpoint_total=0
 for case in quality['rows']:
  name=case['case'];arms={}
  for arm in ['off','on']:
   folder=D/name/arm;audit=read(folder/'complete_event_audit.json');assert audit['complete_group_vacancy_mask_common_snapshot_objective_and_fullgraph_pressure_pass'] and audit['complete_periodic_actual_state_digest_and_final_frame_rebuild_pass'];assert all(sha(k)==h for k,h in audit['bindings'].items());summary=read(folder/'component_summary.json');envelope=read(folder/'arm_cost_envelope.json');receipt=read(folder/'receipt.json');counts=Counter();queries=labels=expanded=groups=0
   for line in (folder/'events.jsonl').open():
    event=json.loads(line);groups+=1
    for net in event['search']['events']:
     for q in net['queries']:queries+=1;counts[q['status']]+=1;labels+=q['labels_created'];expanded+=q['expanded']
   assert groups==audit['groups']==summary['groups'];group_total+=groups;checkpoint_total+=audit['checkpoints'];assert summary['component_seconds']<=receipt['component_seconds']<=envelope['producer_plus_independent_audit_seconds']
   arms[arm]=dict(query_calls=queries,query_status_counts=dict(counts),labels_created=labels,expanded=expanded,overflow=audit['overflow_units'],changed_connection_events=audit['changed_connection_events'],group_counts=summary['counts'],search_loop_component_seconds=summary['component_seconds'],producer_seconds_including_cache_preparation=receipt['component_seconds'],producer_plus_independent_audit_seconds=envelope['producer_plus_independent_audit_seconds'])
   for p in [folder/'complete_event_audit.json',folder/'component_summary.json',folder/'receipt.json',folder/'arm_cost_envelope.json',folder/'events.jsonl',folder/'final_round.json']:bindings[str(p)]=sha(p)
  assert read(D/name/'off/final_round.json')==read(Z/name/'on/final_round.json');cachefile=D/name/'on/bound_cache_stats.json';cache=read(cachefile);bindings[str(cachefile)]=sha(cachefile);bindings[str(Z/name/'on/final_round.json')]=sha(Z/name/'on/final_round.json');a,b=arms['off'],arms['on'];ratio=b['producer_plus_independent_audit_seconds']/a['producer_plus_independent_audit_seconds'];assert ratio>0
  rows.append(dict(case=name,arms=arms,cache=cache,bound_over_zero_producer_audit_time_ratio=ratio,bound_minus_zero_labels=b['labels_created']-a['labels_created'],bound_minus_zero_overflow=b['overflow']-a['overflow'],original_case_gates=case['original_case_gates'],bound_vs_zero_original_gate=case['on_vs_off_original_gate']['native_retained_on']['pass_primary_gate']))
 assert group_total==49906;assert all(sha(k)==h for k,h in bindings.items());result=dict(status='ALL49906_GROUP_EVENTS_WORK_COST_AND_ORIGINAL_QUALITY_ACCOUNTED',audited_group_events=group_total,runtime_state_checkpoints=checkpoint_total,rows=rows,all_bound_cases_pass_original_quality=all(q['original_case_gates']['on'] for q in rows),all_bound_vs_zero_original_gates_pass=all(q['bound_vs_zero_original_gate'] for q in rows),all_cases_lower_producer_audit_time=all(q['bound_over_zero_producer_audit_time_ratio']<1 for q in rows),bindings=bindings,scope='Single fixed development family and ordered paired run. Cache preparation included in producer envelope; shared graph load excluded. Audit time not accelerator runtime. No full paid pipeline, unseen family, full9, native QoR or physical hardware qualification. Overall RouteCast goal remains incomplete.')
 with (D/'research_decision_v1.json').open('x') as out:json.dump(result,out,indent=2);out.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ['bindings','rows']},indent=2))
if __name__=='__main__':main()
