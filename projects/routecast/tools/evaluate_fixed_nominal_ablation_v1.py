"""All12 admitted arms under original full-domain metrics; no relabeled gates."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from evaluate_external_forecast_case_v1 import evaluate
from external_forecast_metrics_v1 import gate
from pre_route_endpoints import sha
D=R/'experiments/prospective_external_family_fixed_nominal_ablation_v1_2026-10-19'
def read(p):return json.loads(p.read_text())
def main():
 terminal=read(D/'terminal.json');assert len(terminal['rows'])==3 and all(c['exit_status']==0 for c in terminal['rows']);protocol=read(D/'protocol.json');assert all(sha(k)==h for k,h in protocol['bindings'].items());results=[];bindings={str(D/'protocol.json'):sha(D/'protocol.json'),str(D/'terminal.json'):sha(D/'terminal.json'),str(Path(__file__)):sha(__file__)}
 for c in protocol['cases']:
  summaries={}
  parity=D/c['case']/'round0_parity.json';assert all(q['round0_events_and_state_and_criticality_equal'] for q in read(parity));bindings[str(parity)]=sha(parity)
  for policy in ('warm_timing_frozen','warm_timing_round_updated'):
   spec=read(Path(c['original_comparison_spec']));pred={}
   for init,name in [('raw_min','raw_min_on'),('native_retained','native_retained_on')]:
    out=D/c['case']/init/policy;proof=out/'complete_event_audit.json';assert read(proof)['complete_round_timing_original_XML_recurrence_component_assembly_and_setup_pass'];pred[name]=dict(frame=str(out/'sketch.json'),proof=str(proof))
   spec.update(case=c['label_case'],source_frame=c['source_frame'],source_proof=c['source_proof'],label_proof=c['label_proof'],label_physical_audit=c['label_physical_audit'],predictions=pred);out=D/c['case']/policy;out.mkdir(exist_ok=False);sp=out/'comparison_spec.json';sp.write_text(json.dumps(spec,indent=2)+'\n');evaluate(sp,out/'comparison.json');summary=read(out/'comparison.json');summaries[policy]=summary;bindings[str(out/'comparison.json')]=sha(out/'comparison.json')
  effects={method:gate(summaries['warm_timing_round_updated']['metrics'][method],summaries['warm_timing_frozen']['metrics'][method]) for method in ('raw_min_on','native_retained_on')};row=dict(case=c['case'],original_case_gates={p:s['pass_case_gate'] for p,s in summaries.items()},metrics={p:s['metrics'] for p,s in summaries.items()},updated_vs_frozen_original_gate=effects);results.append(row);print(json.dumps(dict(case=c['case'],original_case_gates=row['original_case_gates'],updated_vs_frozen_original_gate=effects)),flush=True)
 assert all(sha(k)==h for k,h in bindings.items());(D/'quality_summary_v1.json').write_text(json.dumps(dict(status='ALL12_AUDITED_FIXED_NOMINAL_ABLATION_EVALUATED',rows=results,bindings=bindings,scope='Development fixed nominal timing model only. Full9 availability/family/native utility/paid timing/hardware remain separate.'),indent=2)+'\n')
if __name__=='__main__':main()
