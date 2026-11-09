"""Execute the immutable local-schedule ablation and unchanged original gates."""
import json,sys,subprocess,resource,time
from pathlib import Path
from pre_route_endpoints import sha
from evaluate_external_forecast_case_v1 import evaluate
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_local_schedule_trial_v1_2026-10-20'
def limit():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
def main():
 pp=E/'prince_local_schedule_design_v1_2026-10-20/protocol.json';p=json.loads(pp.read_text());assert all(sha(f)==h for f,h in p['bindings'].items());D.mkdir(exist_ok=False);bindings={str(pp):sha(pp),str(Path(__file__)):sha(__file__)};results=[];tick=time.perf_counter()
 for j in p['jobs']:
  out=Path(j['output']);out.parent.mkdir(parents=True,exist_ok=True)
  with (out.parent/(out.name+'_producer.log')).open('x') as log:code=subprocess.call(j['command'],cwd=R,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limit)
  audit=None;row=dict(case=j['case'],producer_exit_code=code,pass_case_gate=False)
  if code==0:
   with (out.parent/(out.name+'_audit.log')).open('x') as log:audit=subprocess.call(j['audit_command'],cwd=R,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limit)
  row['audit_exit_code']=audit
  if code==0 and audit==0:
   old=E/'prince_feedback_quality_v1_2026-10-20'/j['case']/'specification.json';s=json.loads(old.read_text());s['predictions']['native_retained_on']=dict(frame=str(out/'sketch.json'),proof=str(out/'complete_event_audit_v2.json'));spec=out/'comparison_specification.json';spec.write_text(json.dumps(s,indent=2)+'\n');row['pass_case_gate']=evaluate(spec,out/'comparison.json');row['comparison']=str(out/'comparison.json');bindings[str(old)]=sha(old)
  results.append(row);(D/'progress.json').write_text(json.dumps(dict(rows=results),indent=2)+'\n');print('LOCAL_SCHEDULE',row,flush=True)
 assert all(sha(f)==h for f,h in p['bindings'].items()) and all(sha(f)==h for f,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(rows=results,unavailable=p['unavailable'],bindings=bindings,passed_case_gates=sum(x['pass_case_gate'] for x in results),required_target_cases=9,full9_gate=False,continuous_seconds=time.perf_counter()-tick,strict_unseen_admitted=False,scope='Development scheduling ablation, unchanged original raw_min_on allNET and previous_native controls. No legal route or complete matched native/full-paid gain claim.'),indent=2)+'\n')
if __name__=='__main__':main()
