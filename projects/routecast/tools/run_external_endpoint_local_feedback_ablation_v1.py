"""Frozen three-case endpoint-only feedback scheduling ablation, no parameter sweep."""
import json,sys,time,subprocess,concurrent.futures
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'prospective_external_family_supplementary_development_v1_2026-10-19';O=E/'prospective_external_family_endpoint_local_feedback_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 O.mkdir(exist_ok=False);bindings=closure([Path(__file__)]);cases=[];runner=R/'tools/run_external_native_timing_feedback_v2_2026_10_19.py';auditor=R/'tools/verify_external_current_timing_feedback_events_v1.py'
 for p in [runner,auditor,R/'tools/evaluate_external_forecast_case_v1.py',R/'tools/external_forecast_metrics_v1.py']:bindings[str(p)]=sha(p)
 for i in (1,2,3):
  case=f'w160/episode_{i:02d}';sp=P/'specifications'/case/'comparison_spec.json';spec=read(sp);old_frame=Path(spec['predictions']['native_retained_on']['frame']);old_audit=Path(spec['predictions']['native_retained_on']['proof']);old_protocol=old_frame.parent/'protocol.json';p=read(old_protocol);assert p['rounds']==2 and p['scheduling_policy']=='all_NETs_each_round';warm=Path(p['warm_seed_proof']).parent;warm_proof=read(warm/'verification.json');assert all(sha(q)==h for q,h in warm_proof['bindings'].items());assert read(old_audit)['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'];out=O/'predictions'/case;assert not out.exists();proof=out/'complete_event_audit.json';predict=[sys.executable,str(runner),spec['endpoint'],str(out),p['structural_node_base_proof'],str(Path(p['criticality_input_proof']).parent),str(warm),'local'];audit=[sys.executable,str(auditor),str(out),case+'_endpoint_local',str(proof)];cases.append(dict(case=case,endpoint=spec['endpoint'],base_frame=str(old_frame),original_comparison_spec=str(sp),candidate_frame=str(out/'sketch.json'),candidate_proof=str(proof),warm_frame=str(warm/'initial.json'),dirty_NETs=warm_proof['dirty_nets'],predict_command=predict,audit_command=audit))
  for q in [sp,old_frame,old_audit,old_protocol,warm/'verification.json',warm/'initial.json',Path(spec['endpoint'])]:bindings[str(q)]=sha(q)
 policy='All3 already exposed width160 development cases; single fixed change from original all-NET two-round feedback to endpoint_closure_NETs_each_round (local), starting from identical original native_retained warm seeds. Same current perpin criticality, structural base/static span/history/present prices, original hard per-CID budgets, retained-tree rules and overflow/objective transaction guards. Exactly2 rounds, no NET/parameter/order/candidate sweep. No clean NET rescheduling. Original all4 forecast metric gate vs previous_native/raw_min_on, fixed full domains and K unchanged; original all-NET final candidate as supplementary diagnosis. Freeze before outputs/labels; reuse old cold development labels only after complete event/XML audit. All six unavailable source cases retained; no full9, strict-unseen, native utility, matched full-time or hardware success.'
 pp=O/'protocol.json';pp.write_text(json.dumps(dict(policy=policy,cases=cases,bindings=bindings,unavailable_cases=[f'w{w:03d}/episode_{i:02d}' for w in (96,128) for i in (1,2,3)]),indent=2)+'\n');bindings[str(pp)]=sha(pp)
 def run_case(spec):
  rows=[]
  for stage,key in [('predict','predict_command'),('audit','audit_command')]:
   log=O/'logs'/spec['case']/(stage+'.log');log.parent.mkdir(parents=True,exist_ok=True);start=time.perf_counter();print('LOCAL_ABLATION_STAGE_START',spec['case'],stage,flush=True)
   with log.open('x') as handle:proc=subprocess.run(spec[key],cwd=R,stdout=handle,stderr=subprocess.STDOUT)
   row=dict(case=spec['case'],stage=stage,exit_code=proc.returncode,wall_seconds=time.perf_counter()-start,log=str(log),log_sha256=sha(log));rows.append(row);print('LOCAL_ABLATION_STAGE_TERMINAL',spec['case'],stage,proc.returncode,flush=True)
   if proc.returncode:break
  return dict(case=spec['case'],stages=rows,complete=all(r['exit_code']==0 for r in rows) and len(rows)==2)
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run_case,cases))
 assert all(sha(p)==h for p,h in bindings.items());(O/'execution_receipt.json').write_text(json.dumps(dict(status='ALL3_LOCAL_PREDICTION_AND_AUDIT_STAGES_TERMINAL',rows=rows,all_complete=all(r['complete'] for r in rows),bindings=bindings,scope='Stage wall times include process overhead but not all prior input/source/warm/native costs; concurrent per-case walls are not matched end-to-end runtime or speedup.'),indent=2)+'\n');print('LOCAL_ABLATION_ALL_TERMINAL',all(r['complete'] for r in rows),flush=True)
if __name__=='__main__':main()
