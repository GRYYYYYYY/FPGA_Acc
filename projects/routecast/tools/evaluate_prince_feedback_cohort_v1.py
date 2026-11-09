"""Original fixed metric/gates on six available targets; all9 availability retained."""
import json,sys,time
from pathlib import Path
from pre_route_endpoints import sha
from evaluate_external_forecast_case_v1 import evaluate
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_feedback_quality_v1_2026-10-20';F=E/'prince_feedback_cohort_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);specs=[];unavailable=[f'w096/episode_{i:02d}' for i in [1,2,3]]
 for w in [128,160]:
  for i in [1,2,3]:
   case=f'w{w}/episode_{i:02d}';native=E/'prince_native_cohort_v1_2026-10-20'/case;canonical=E/'prince_native_canonical_v1_2026-10-20'/case/'verification.json';c=json.loads(canonical.read_text());assert c['semantic_consistency_gate_pass'] and c['original_zero_counter_gate_pass'];physical=native/'physical_audit.json';assert json.loads(physical.read_text())['overflow_units']==0
   out=D/case;out.mkdir(parents=True);label=out/'label_admission.json';paths=[canonical,native/'receipt.json',physical,native/'pre_route_endpoints.json'];bindings={str(p):sha(p) for p in paths};bindings.update(c['files']);label.write_text(json.dumps(dict(case=case,status='FULL_PHYSICAL_AND_CANONICAL_PASS',canonical=c,bindings=bindings,scope='Composite existing independent physical/native and canonical evidence; no rerouting or label modification.'),indent=2)+'\n')
   source=E/'prince_native_source_checkpoints_v1_2026-10-20'/f'w{w}';spec=out/'specification.json';spec.write_text(json.dumps(dict(schema='ROUTECAST_EXTERNAL_FORECAST_CASE_V1',case=case,endpoint=str(native/'pre_route_endpoints.json'),domain_proof=str(E/'prince_quality_domains_v1_2026-10-20'/f'w{w}'/'verification.json'),domain_independent_proof=str(E/'prince_quality_domains_v1_2026-10-20/independent_verification_v1.json'),source_proof=str(source/'independent_xml_verification_v1.json'),source_frame=str(source/'initial.json'),predictions={method:dict(frame=str(F/case/arm/'sketch.json'),proof=str(F/case/arm/'complete_event_audit_v2.json')) for method,arm in [('raw_min_on','raw_min'),('native_retained_on','native_retained')]},label_proof=str(label),label_physical_audit=str(physical)),indent=2)+'\n');specs.append((case,spec,out/'comparison.json'))
 bindings={str(p):sha(p) for p in [Path(__file__),R/'tools/evaluate_external_forecast_case_v1.py',R/'tools/external_forecast_metrics_v1.py',*[s for c,s,o in specs]]};(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,unavailable=unavailable,policy='Original all4 metrics nonregress+one strict percontrol; previous_native and original raw_min_on controls, rho epsilon1e-12, all9 mandatory. Development exposed, no tuning or strict unseen admission.'),indent=2)+'\n');rows=[]
 for case,spec,out in specs:
  data=json.loads(spec.read_text())
  while not all(Path(a['proof']).exists() for a in data['predictions'].values()):
   if (F/'audit_receipt_v2.json').exists():break
   time.sleep(1)
  try:passed=evaluate(spec,out);row=dict(case=case,pass_case_gate=passed,comparison=str(out))
  except Exception as exc:row=dict(case=case,pass_case_gate=False,error=repr(exc))
  rows.append(row);print('PRINCE_QUALITY',case,row,flush=True)
 assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(rows=rows,unavailable=unavailable,passed_case_gates=sum(r['pass_case_gate'] for r in rows),required_target_cases=9,full9_availability=False,full9_gate=False,bindings=bindings,strict_unseen_admitted=False,scope='Development forecast comparison only; incomplete width96 native label availability fails original full9 gate. Native utility/full paid gain and physical timing remain unproven.'),indent=2)+'\n')
if __name__=='__main__':main()
