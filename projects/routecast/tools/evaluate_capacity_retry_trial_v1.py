"""Original domains/labels/gates, retry against off and existing raw-min control."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from evaluate_external_forecast_case_v1 import evaluate
from external_forecast_metrics_v1 import gate
from pre_route_endpoints import sha
D=R/'experiments/prospective_external_family_capacity_retry_v1_2026-10-20';A=R/'experiments/prospective_external_family_fixed_nominal_ablation_v1_2026-10-19'
def read(p):return json.loads(p.read_text())
def main():
 t=read(D/'terminal.json');assert len(t['rows'])==3 and all(q['exit_status']==0 for q in t['rows']);protocol=read(D/'protocol.json');assert all(sha(k)==h for k,h in protocol['bindings'].items());rows=[];bindings={str(D/'terminal.json'):sha(D/'terminal.json'),str(D/'protocol.json'):sha(D/'protocol.json'),str(Path(__file__).resolve()):sha(__file__)}
 for c in protocol['cases']:
  assert read(D/c['case']/'off_parity.json')['status']=='OFF_FULL_STATES_EVENTS_AND_TIMING_EXACT_ARCHIVED_BASELINE';metrics={};gates={};retry_stats={}
  for arm in ('off','on'):
   out=D/c['case']/arm;proof=out/'complete_event_audit.json';assert read(proof)['complete_capacity_retry_original_and_secondary_mask_budget_common_objective_and_selection_pass'];raw=A/c['case']/'raw_min/warm_timing_round_updated';spec=read(Path(c['original_comparison_spec']));spec.update(case=c['label_case'],source_frame=c['source_frame'],source_proof=c['source_proof'],label_proof=c['label_proof'],label_physical_audit=c['label_physical_audit'],predictions=dict(native_retained_on=dict(frame=str(out/'sketch.json'),proof=str(proof)),raw_min_on=dict(frame=str(raw/'sketch.json'),proof=str(raw/'complete_event_audit.json'))));sp=out/'comparison_spec.json';sp.write_text(json.dumps(spec,indent=2)+'\n');evaluate(sp,out/'comparison.json');result=read(out/'comparison.json');metrics[arm]=result['metrics'];gates[arm]=result['pass_case_gate'];bindings[str(out/'comparison.json')]=sha(out/'comparison.json');events=[e for rr in read(out/'receipt.json')['rounds'] for e in rr['events']];retries=[e['capacity_retry'] for e in events if 'capacity_retry' in e];retry_stats[arm]=dict(triggered=len(retries),complete=sum(x['secondary_candidate'] is not None for x in retries),selected=sum(x['selected'] for x in retries),overflow=read(out/'sketch.json')['overflow_units'])
  effects={name:gate(metrics['on'][name],metrics['off'][name]) for name in ('native_retained_on','raw_min_on')};row=dict(case=c['case'],original_case_gates=gates,metrics=metrics,on_vs_off_original_gate=effects,retry_stats=retry_stats);rows.append(row);print(json.dumps(dict(case=c['case'],original_case_gates=gates,on_vs_off_original_gate=effects,retry_stats=retry_stats)),flush=True)
 assert all(sha(k)==h for k,h in bindings.items());(D/'quality_summary_v1.json').write_text(json.dumps(dict(status='ALL6_CAPACITY_RETRY_ARMS_ORIGINAL_METRICS_EVALUATED',rows=rows,bindings=bindings,scope='Development study only. Raw control from already audited matching timing policy. Full9/native utility/paid timing/hardware remain open.'),indent=2)+'\n')
if __name__=='__main__':main()
