"""Frozen paired feedback development run; all9 cases retained, no target labels read."""
import json,sys,subprocess,resource,time
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_feedback_cohort_v1_2026-10-20'
def limit():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
def main():
 D.mkdir(exist_ok=False);jobs=[];unavailable=[];producer=R/'tools/run_prince_native_timing_feedback_v1.py';verifier=R/'tools/verify_prince_current_timing_feedback_events_v1.py';paths=[Path(__file__),producer,verifier,E/'prince_frame_timings_v1_2026-10-20/adapter_contract_verification_v1.json',E/'prince_warm_initializers_v1_2026-10-20/receipt.json']
 for width in [96,128,160]:
  for episode in [1,2,3]:
   case=f'w{width:03d}/episode_{episode:02d}'
   if width==96:unavailable.append(dict(case=case,reason='missing_legal_source_checkpoint'));continue
   ep=E/'prince_native_cohort_v1_2026-10-20'/case/'pre_route_endpoints.json';base=E/'prince_width_node_bases_v1_2026-10-20'/f'w{width}'/'verification.json';timing=E/'prince_frame_timings_v1_2026-10-20'/case
   for arm in ['raw_min','native_retained']:
    warm=E/'prince_warm_initializers_v1_2026-10-20'/case/arm;out=D/case/arm;cmd=[sys.executable,str(producer),str(ep),str(out),str(base),str(timing),str(warm),'all'];audit=[sys.executable,str(verifier),str(out),case+'_'+arm,str(out/'complete_event_audit.json')];jobs.append(dict(case=case,arm=arm,output=str(out),command=cmd,audit_command=audit));paths.extend([ep,base,timing/'verification.json',warm/'verification.json'])
 bindings={str(p):sha(p) for p in paths};(D/'protocol.json').write_text(json.dumps(dict(jobs=jobs,unavailable=unavailable,bindings=bindings,policy='Same frozen original two-round feedback algorithm in both arms, allNET schedule, original linear fallback and transaction guards. Only schema-bound PRINCE timing adapter changed. All9 cases retained. No target route or occupancy files passed to predictor; no retries or outcome-driven tuning. Complete independent event audit required. Diagnostic component clocks, no matched full-paid speedup or unseen claim.'),indent=2)+'\n');results=[];start=time.perf_counter()
 for j in jobs:
  out=Path(j['output']);out.parent.mkdir(parents=True,exist_ok=True);tick=time.perf_counter()
  with (out.parent/(j['arm']+'_predict.log')).open('x') as f:code=subprocess.call(j['command'],stdout=f,stderr=subprocess.STDOUT,cwd=R,preexec_fn=limit)
  audit=None
  if code==0:
   with (out.parent/(j['arm']+'_audit.log')).open('x') as f:audit=subprocess.call(j['audit_command'],stdout=f,stderr=subprocess.STDOUT,cwd=R,preexec_fn=limit)
  result=dict(case=j['case'],arm=j['arm'],predict_exit_code=code,audit_exit_code=audit,seconds=time.perf_counter()-tick,complete_event_audit_pass=code==0 and audit==0);results.append(result);(D/'progress.json').write_text(json.dumps(dict(results=results,unavailable=unavailable),indent=2)+'\n');print('PRINCE_FEEDBACK',j['case'],j['arm'],code,audit,flush=True)
 assert all(sha(p)==h for p,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(results=results,unavailable=unavailable,continuous_seconds=time.perf_counter()-start,bindings=bindings,forecast_quality_pending=True,strict_unseen_admitted=False),indent=2)+'\n')
if __name__=='__main__':main()
