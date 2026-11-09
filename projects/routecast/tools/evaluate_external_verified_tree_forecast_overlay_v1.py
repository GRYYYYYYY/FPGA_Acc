"""One fixed original-metric comparison of already audited development overlays."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from evaluate_external_forecast_case_v1 import evaluate
from external_forecast_metrics_v1 import gate
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_verified_tree_forecast_overlay_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 proof=D/'independent_verification_v1.json';v=read(proof);assert v['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'];assert all(sha(p)==h for p,h in v['bindings'].items());protocol=read(D/'protocol.json');bindings={str(p):sha(p) for p in [proof,D/'protocol.json',Path(__file__).resolve(),R/'tools/evaluate_external_forecast_case_v1.py',R/'tools/external_forecast_metrics_v1.py']};rows=[]
 for item in protocol['cases']:
  case=item['case'];out=D/case;spec=read(item['original_comparison_spec']);spec['predictions']['native_retained_on']=dict(frame=str(out/'frame.json'),proof=str(proof));spec['development_scope']='Fixed verified tree overlay, already exposed labels, no strict unseen or utility claim.';sp=out/'comparison_spec.json';assert not sp.exists();sp.write_text(json.dumps(spec,indent=2)+'\n');rp=out/'comparison.json';passed=evaluate(sp,rp);result=read(rp);original=Path(item['base_frame']).parent.parent/'comparison.json';old=read(original);assert old['case']==case and all(sha(p)==h for p,h in old['bindings'].items());vs_old=gate(result['metrics']['native_retained_on'],old['metrics']['native_retained_on']);m=result['metrics']['native_retained_on'];row=dict(case=case,original_registered_case_gate=passed,vs_previous_and_raw_controls=result['checks'],vs_original_candidate=vs_old,candidate_metrics={scope:{k:m[scope][k] for k in ['spearman','top_k_hits','k','universe_size']} for scope in ['resource','spatial']},original_candidate_metrics={scope:{k:old['metrics']['native_retained_on'][scope][k] for k in ['spearman','top_k_hits','k','universe_size']} for scope in ['resource','spatial']});rows.append(row)
  for p in [sp,rp,original]:bindings[str(p)]=sha(p)
  print('VERIFIED_TREE_FORECAST_QUALITY',json.dumps(row),flush=True)
 assert all(sha(p)==h for p,h in bindings.items());p=D/'quality_summary.json';assert not p.exists();p.write_text(json.dumps(dict(status='ALL3_FIXED_DEVELOPMENT_OVERLAY_ORIGINAL_FORECAST_METRICS_EVALUATED',rows=rows,all3_original_case_gates_pass=all(r['original_registered_case_gate'] for r in rows),all9_availability_gate_pass=False,unavailable_cases=protocol['unavailable_cases'],bindings=bindings,scope='Already exposed development labels. Original all4 nonregress plus1strict against each previous_native/raw_min_on control unchanged. Vs old candidate is additional diagnosis only. Forecast overload is allowed, not an independent reason to fail ranking. No original full9/strict-family/native-utility/full-time or hardware claim.'),indent=2)+'\n')
if __name__=='__main__':main()
