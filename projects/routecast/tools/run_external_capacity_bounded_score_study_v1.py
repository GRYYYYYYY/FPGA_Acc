"""Freeze a single analytic score transform, then evaluate same3 development cases."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from evaluate_external_capacity_bounded_score_case_v1 import evaluate
from external_forecast_metrics_v1 import gate
R=Path(__file__).resolve().parents[1];E=R/'experiments';L=E/'prospective_external_family_endpoint_local_feedback_v1_2026-10-19';O=E/'prospective_external_family_capacity_bounded_utilization_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 O.mkdir(exist_ok=False);bindings=closure([Path(__file__)]);cases=[]
 for item in read(L/'protocol.json')['cases']:
  sp=L/item['case']/'comparison_spec.json';spec=read(sp);audit=read(item['candidate_proof']);assert audit['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'] and all(sha(p)==h for p,h in audit['bindings'].items());assert audit['bindings'][item['candidate_frame']]==sha(item['candidate_frame']);cases.append(dict(case=item['case'],endpoint=item['endpoint'],base_frame=item['base_frame'],candidate_frame=item['candidate_frame'],candidate_proof=item['candidate_proof'],original_comparison_spec=str(sp)))
  for p in [sp,Path(item['candidate_frame']),Path(item['candidate_proof']),Path(item['base_frame'])]:bindings[str(p)]=sha(p)
 policy='One explicit new analytic utilization-score head applied to endpoint-local2round demand for ALL3 exposed cases: min(raw unique-NET count, physical capacity) per CHANNEL, then same inclusive spatial aggregation. No tuned coefficient or threshold, source/NET selection, reroute or label change. Original raw frame ledgers/paths/budgets/epochs remain byte-unchanged; bounded counts are ONLY forecast scores, never submitted as physical ledger. Original previous_native/raw_min_on controls and graph universes/K/four metric gate unchanged; original all-NET candidate is secondary diagnosis. Original direct-demand failures retained. No strict-unseen/all9/native utility/matched full-time/hardware claim.'
 pp=O/'protocol.json';pp.write_text(json.dumps(dict(policy=policy,cases=cases,bindings=bindings,unavailable_cases=[f'w{w:03d}/episode_{i:02d}' for w in (96,128) for i in (1,2,3)]),indent=2)+'\n');bindings[str(pp)]=sha(pp);rows=[]
 for item in cases:
  out=O/item['case'];out.mkdir(parents=True);spec=read(item['original_comparison_spec']);spec['schema']='ROUTECAST_EXTERNAL_CAPACITY_BOUNDED_UTILIZATION_SCORE_CASE_V1';spec['score_head']='CAPACITY_BOUNDED_UTILIZATION_V1';sp=out/'comparison_spec.json';sp.write_text(json.dumps(spec,indent=2)+'\n');rp=out/'comparison.json';passed=evaluate(sp,rp);result=read(rp);oldp=Path(item['base_frame']).parent.parent/'comparison.json';old=read(oldp);m=result['metrics']['native_retained_on'];rows.append(dict(case=item['case'],original_registered_case_gate=passed,vs_previous_and_raw_controls=result['checks'],vs_original_candidate=gate(m,old['metrics']['native_retained_on']),candidate_metrics={scope:{k:m[scope][k] for k in ['spearman','top_k_hits','k','universe_size']} for scope in ['resource','spatial']},original_candidate_metrics={scope:{k:old['metrics']['native_retained_on'][scope][k] for k in ['spearman','top_k_hits','k','universe_size']} for scope in ['resource','spatial']}))
  for p in [sp,rp,oldp]:bindings[str(p)]=sha(p)
  print('BOUNDED_UTILIZATION_QUALITY',json.dumps(rows[-1]),flush=True)
 assert all(sha(p)==h for p,h in bindings.items());(O/'quality_summary.json').write_text(json.dumps(dict(status='ALL3_FIXED_CAPACITY_BOUNDED_SCORE_HEAD_ORIGINAL_FORECAST_METRICS_EVALUATED',rows=rows,all3_original_case_gates_pass=all(r['original_registered_case_gate'] for r in rows),all9_availability_gate_pass=False,unavailable_cases=read(pp)['unavailable_cases'],bindings=bindings,scope=policy),indent=2)+'\n')
if __name__=='__main__':main()
