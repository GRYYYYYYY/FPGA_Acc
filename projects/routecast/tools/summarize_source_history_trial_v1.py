"""All12 event/source-history/baseline/metric/cost evidence, terminal-only."""
import json
from pathlib import Path
import sys
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
E=R/'experiments';D=E/'prospective_external_family_source_history_trial_v1_2026-10-20';A=E/'prospective_external_family_fixed_nominal_ablation_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 assert read(D/'evaluation_terminal.json')['exit_status']==0;terminal=read(D/'terminal.json');assert len(terminal['rows'])==3 and all(q['exit_status']==0 for q in terminal['rows']);quality=read(D/'quality_summary_v1.json');metric=read(D/'independent_metrics_verification_v1.json');assert metric['status']=='ALL36_ABLATION_CONTROL_METRIC_VECTORS_AND_ORIGINAL_GATES_VERIFIED';protocol=read(D/'protocol.json');assert len(protocol['unavailable_cases'])==6 and not protocol['all9_availability_pass'];prior=read(protocol['source_prior']);bindings={str(Path(__file__)):sha(__file__)}
 for p in [D/'protocol.json',D/'terminal.json',D/'evaluation_terminal.json',D/'quality_summary_v1.json',D/'independent_metrics_verification_v1.json']:
  q=read(p);assert all(sha(k)==h for k,h in q.get('bindings',{}).items());bindings[str(p)]=sha(p)
 rows=[];events=0
 required=['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass','complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass','complete_same_snapshot_objective_guard_and_retained_state_pass','complete_present_snapshot_owner_exclusion_and_union_objective_pass','complete_round_timing_original_XML_recurrence_component_assembly_and_setup_pass']
 for row in quality['rows']:
  case=row['case'];stats={}
  for init in ['raw_min','native_retained']:
   arms={};folder=D/case/init
   for arm in ['off','on']:
    out=folder/arm;audit=read(out/'complete_event_audit.json');assert all(audit[k] for k in required);assert all(sha(k)==h for k,h in audit['bindings'].items());assert audit['events']==11838 and audit['completed']==15616;events+=audit['events'];r=read(out/'receipt.json');h=read(out/'source_initial_history.json');assert h==(prior['history'] if arm=='on' else {});assert read(out/'initial.json')==read(A/case/init/'warm_timing_round_updated/initial.json')
    if arm=='off':
     for name in ['round0.json','round1.json','sketch.json']:assert read(out/name)==read(A/case/init/'warm_timing_round_updated'/name)
    arms[arm]=dict(overflow=audit['overflow_units'],committed=audit['committed'],retained=audit['retained'],changed_tree_events=audit['changed_trees'],producer_seconds=r['total_paid_resident_seconds'],setup_seconds=r['model_setup_seconds'],search_seconds=r['search_seconds'],fallback_seconds=r['fallback_seconds'],initial_frame_unchanged=True,source_nonzero_history_nodes=len(h))
    for p in [out/'complete_event_audit.json',out/'receipt.json',out/'source_initial_history.json',out/'round0.json',out/'round1.json',out/'sketch.json']:bindings[str(p)]=sha(p)
   arms['on_over_off_producer_time_ratio']=arms['on']['producer_seconds']/arms['off']['producer_seconds'];stats[init]=arms
  rows.append(dict(case=case,original_case_gates=row['original_case_gates'],source_history_on_vs_off_original_gates={k:v['pass_primary_gate'] for k,v in row['source_history_on_vs_off_original_gate'].items()},arms=stats))
 assert events==142056 and all(sha(k)==h for k,h in bindings.items());result=dict(status='ALL142056_NET_EVENTS_SOURCE_HISTORY_BASELINE_AND36_METRICS_ACCOUNTED',rows=rows,events=events,off_baseline_reproduced_all6=True,source_prior_only=True,all_original_on_case_gates_pass=all(q['original_case_gates']['on'] for q in rows),all_on_vs_off_native_gates_pass=all(q['source_history_on_vs_off_original_gates']['native_retained_on'] for q in rows),bindings=bindings,scope='Single development family, fixed nominal timing limitations retained. Producer timings include per-arm graph/setup but exclude independent audit and common source-native run/history export, conversions/transfers/native finishing; no full paid time or net-benefit admission. Full9 availability, unseen families, native QoR and physical hardware still separate. Overall goal remains active.')
 with (D/'research_decision_v1.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ['bindings','rows']},indent=2))
if __name__=='__main__':main()
