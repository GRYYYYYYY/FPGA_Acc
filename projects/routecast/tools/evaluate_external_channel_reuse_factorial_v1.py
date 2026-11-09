"""Frozen initializer x score-head factorial, all cases retained, no winner selection."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from source_binding_v2 import closure
from pre_route_endpoints import sha
from evaluate_external_forecast_case_v1 import evaluate as raw_evaluate
from evaluate_external_capacity_bounded_score_case_v1 import evaluate as bounded_evaluate
from external_forecast_metrics_v1 import gate
R=Path(__file__).resolve().parents[1];E=R/'experiments';I=E/'prospective_external_family_native_channel_reuse_warm_v1_2026-10-19';W=E/'prospective_external_family_zero_feedback_warm_v1_2026-10-19';O=E/'prospective_external_family_channel_reuse_factorial_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 O.mkdir(exist_ok=False);bindings=closure([Path(__file__)]);protocol=read(I/'protocol.json');assert protocol['score_plan']=={'initializers':['original_audited_warm','native_channel_reuse_warm'],'score_heads':['raw_demand','capacity_bounded_utilization'],'all_cases_required':True};ip=I/'independent_verification_v1.json';wp=W/'independent_verification_v1.json'
 for p in [ip,wp]:
  a=read(p);assert a['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'] and all(sha(q)==h for q,h in a['bindings'].items());bindings[str(p)]=sha(p)
 bindings[str(I/'protocol.json')]=sha(I/'protocol.json');cases=[]
 for item in protocol['cases']:
  case=item['case'];original=read(item['original_comparison_spec']);global_frame=original['predictions']['native_retained_on']['frame'];arms=[]
  for init,frame,proof in [('original_audited_warm',item['base_frame'],wp),('native_channel_reuse_warm',str(I/case/'frame.json'),ip)]:
   assert read(proof)['bindings'][frame]==sha(frame)
   for head in ['raw_demand','capacity_bounded_utilization']:arms.append(dict(initializer=init,head=head,frame=frame,proof=str(proof)))
  cases.append(dict(case=case,original_spec=item['original_comparison_spec'],original_global_frame=global_frame,arms=arms));bindings[item['original_comparison_spec']]=sha(item['original_comparison_spec'])
 pp=O/'protocol.json';pp.write_text(json.dumps(dict(cases=cases,bindings=bindings,producer_score_plan_frozen_before_candidate_generation=True,policy='All3 exposed cases, fixed2x2 factorial original-warm vs native-channel-reuse-warm and raw-demand vs analytic capacity-bounded utilization. No per-case winner or coefficient/threshold/NET search. Identical old warm raw arm reuses independently verified published metrics only after exact candidate bytes and control/label/domain identity checks. Original previous_native/raw_min_on controls, metrics/K/domains/gates unchanged. Raw physical ledgers never clipped. No native/full9/unseen/time/hardware promotion.',unavailable_cases=protocol['unavailable_cases']),indent=2)+'\n');bindings[str(pp)]=sha(pp);rows=[]
 for spec in cases:
  original=read(spec['original_spec']);global_comparison=Path(spec['original_global_frame']).parent.parent/'comparison.json';global_metrics=read(global_comparison)['metrics']['native_retained_on'];bindings[str(global_comparison)]=sha(global_comparison)
  for arm in spec['arms']:
   out=O/spec['case']/arm['initializer']/arm['head'];out.mkdir(parents=True);s=read(spec['original_spec']);s['predictions']['native_retained_on']=dict(frame=arm['frame'],proof=arm['proof']);s['schema']='ROUTECAST_EXTERNAL_FORECAST_CASE_V1' if arm['head']=='raw_demand' else 'ROUTECAST_EXTERNAL_CAPACITY_BOUNDED_UTILIZATION_SCORE_CASE_V1';s['score_head']=arm['head'];sp=out/'comparison_spec.json';sp.write_text(json.dumps(s,indent=2)+'\n');rp=out/'comparison.json';reused=False
   if arm['initializer']=='original_audited_warm' and arm['head']=='raw_demand':
    oldsp=W/spec['case']/'comparison_spec.json';oldspec=read(oldsp);assert Path(arm['frame']).read_bytes()==Path(oldspec['predictions']['native_retained_on']['frame']).read_bytes();assert all(s[k]==oldspec[k] for k in ['case','endpoint','domain_proof','domain_independent_proof','source_frame','source_proof','label_proof','label_physical_audit']);assert s['predictions']['raw_min_on']==oldspec['predictions']['raw_min_on'];oldrp=W/spec['case']/'comparison.json';result=read(oldrp);assert all(sha(p)==h for p,h in result['bindings'].items());bindings[str(oldrp)]=sha(oldrp);rp.write_bytes(oldrp.read_bytes());reused=True
   else:
    (raw_evaluate if arm['head']=='raw_demand' else bounded_evaluate)(sp,rp);result=read(rp)
   m=result['metrics']['native_retained_on'];row=dict(case=spec['case'],initializer=arm['initializer'],head=arm['head'],comparison=str(rp),comparison_spec=str(sp),reused_old_warm_raw_metrics=reused,original_registered_case_gate=result['pass_case_gate'],vs_original_global_candidate=gate(m,global_metrics),candidate_metrics={scope:{k:m[scope][k] for k in ['spearman','top_k_hits','k','universe_size']} for scope in ['resource','spatial']});rows.append(row)
   for p in [rp,sp]:bindings[str(p)]=sha(p)
   print('CHANNEL_REUSE_FACTORIAL',json.dumps(row),flush=True)
 assert all(sha(p)==h for p,h in bindings.items());(O/'quality_summary.json').write_text(json.dumps(dict(status='ALL12_FROZEN_CHANNEL_REUSE_FACTORIAL_ARMS_EVALUATED',rows=rows,all9_availability_pass=False,unavailable_cases=protocol['unavailable_cases'],bindings=bindings,scope='Development factorial, no model or case winner selection. Reused old warm raw metrics keep original receipts; no repeated search or performance inference. All original quality and broader research obligations remain.'),indent=2)+'\n')
if __name__=='__main__':main()
