"""Original forecast gates for all6 refinement arms; archival raw reference unchanged."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from evaluate_external_forecast_case_v1 import evaluate
from external_forecast_metrics_v1 import gate
E=R/'experiments';D=E/'prospective_external_family_sequential_group_refinement_v1_2026-10-20';A=E/'prospective_external_family_fixed_nominal_ablation_v1_2026-10-19'
def read(p):return json.loads(p.read_text())
def main():
 terminal=read(D/'terminal.json');assert len(terminal['rows'])==3 and all(q['exit_status']==0 for q in terminal['rows']);protocol=read(D/'protocol.json');assert all(sha(k)==h for k,h in protocol['bindings'].items());bindings={str(D/'terminal.json'):sha(D/'terminal.json'),str(D/'protocol.json'):sha(D/'protocol.json'),str(Path(__file__).resolve()):sha(__file__)};rows=[]
 for c in protocol['cases']:
  case=c['case'];baseline=A/case/'native_retained/warm_timing_round_updated';assert read(D/case/'off/final_round.json')==read(baseline/'round1.json');assert read(D/case/'off/sketch.json')==read(baseline/'sketch.json');metrics={};gates={};stats={}
  for arm in ('off','on'):
   out=D/case/arm;proof=out/'complete_event_audit.json';audit=read(proof);assert audit['complete_group_vacancy_mask_common_snapshot_objective_and_fullgraph_pressure_pass'] and audit['complete_periodic_actual_state_digest_and_final_frame_rebuild_pass'];raw=A/case/'raw_min/warm_timing_round_updated';spec=read(Path(c['original_comparison_spec']));spec.update(case=c['label_case'],source_frame=c['source_frame'],source_proof=c['source_proof'],label_proof=c['label_proof'],label_physical_audit=c['label_physical_audit'],predictions=dict(native_retained_on=dict(frame=str(out/'sketch.json'),proof=str(proof)),raw_min_on=dict(frame=str(raw/'sketch.json'),proof=str(raw/'complete_event_audit.json'))));sp=out/'comparison_spec.json';sp.write_text(json.dumps(spec,indent=2)+'\n');evaluate(sp,out/'comparison.json');result=read(out/'comparison.json');metrics[arm]=result['metrics'];gates[arm]=result['pass_case_gate'];summary=read(out/'component_summary.json');stats[arm]=dict(groups=summary['groups'],counts=summary['counts'],overflow=audit['overflow_units'],changed_connection_events=audit['changed_connection_events'],component_seconds=summary['component_seconds']);bindings[str(out/'comparison.json')]=sha(out/'comparison.json')
  effects={name:gate(metrics['on'][name],metrics['off'][name]) for name in ('native_retained_on','raw_min_on')};row=dict(case=case,original_case_gates=gates,metrics=metrics,on_vs_off_original_gate=effects,refinement_stats=stats);rows.append(row);print(json.dumps(dict(case=case,original_case_gates=gates,on_vs_off_original_gate=effects,refinement_stats=stats)),flush=True)
 assert all(sha(k)==h for k,h in bindings.items());(D/'quality_summary_v1.json').write_text(json.dumps(dict(status='ALL6_SEQUENTIAL_GROUP_REFINEMENT_ARMS_ORIGINAL_METRICS_EVALUATED',rows=rows,bindings=bindings,scope='Causal comparison is matched group-refinement on/off; raw_min is archival reference, no matched-initializer group-policy claim. Component timing only, not full paid pipeline. Full9/family/native QoR/hardware gaps unchanged.'),indent=2)+'\n')
if __name__=='__main__':main()
