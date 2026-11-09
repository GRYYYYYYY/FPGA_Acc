"""Single-owner prerequisite wait and full source-history trial, no restarts."""
import sys,os,time,json,subprocess,datetime
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from source_binding_v2 import closure
from pre_route_endpoints import sha
E=R/'experiments';D=E/'source_history_trial_launch_chain_v1_2026-10-20';T=E/'prospective_external_family_source_history_trial_v1_2026-10-20';P=E/'source_history_real_pipeline_contract_v1_2026-10-20/verification.json'
def ticks(pid):
 try:return Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[19]
 except FileNotFoundError:return None
def main():
 pid=int(sys.argv[1]);identity=sys.argv[2];assert ticks(pid)==identity and not T.exists();D.mkdir(exist_ok=False);scripts=[Path(__file__),R/'tools/run_source_history_trial_v1.py',R/'tools/run_source_history_case_v1.py',R/'tools/run_external_source_history_feedback_v1.py',R/'tools/verify_external_source_history_feedback_events_v1.py',R/'tools/evaluate_source_history_trial_v1.py',R/'tools/verify_source_history_trial_metrics_v1.py'];bindings=closure(scripts);(D/'protocol.json').write_text(json.dumps(dict(source_pid=pid,source_startticks=identity,bindings=bindings,policy='Wait same first-case pipeline only. Require full off/on qualification proof and unchanged hashes before all3x2initializerx2history trial. No restarts or metrics until all full audits.'),indent=2)+'\n')
 def save(status,**extra):
  p=D/'state.json';tmp=p.with_suffix('.json.tmp');tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**extra),indent=2)+'\n');os.replace(tmp,p);print(status,flush=True)
 save('WAITING_ORIGINAL_PIPELINE',source_pid=pid)
 while ticks(pid)==identity:time.sleep(10)
 if not P.exists():save('STOPPED_PREREQUISITE_WITHOUT_VERIFICATION');sys.exit(1)
 v=json.loads(P.read_text());assert v['status']=='FULL_FIRST_CASE_SOURCE_HISTORY_OFF_PARITY_ON_EVENT_PIPELINE_PASS';assert all(sha(k)==h for k,h in v['bindings'].items()) and all(sha(k)==h for k,h in bindings.items());assert not T.exists();save('RUNNING_FULL_ALL3_SOURCE_HISTORY_TRIAL')
 with (D/'trial.log').open('x') as log:code=subprocess.run([sys.executable,str(R/'tools/run_source_history_trial_v1.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
 if code:save('STOPPED_TRIAL_OR_EVALUATION_FAILURE',exit_status=code);sys.exit(code)
 terminal=json.loads((T/'evaluation_terminal.json').read_text());assert terminal['exit_status']==0;save('FULL_TRIAL_AND_INDEPENDENT_METRICS_TERMINAL',exit_status=0,scope='Experiment terminal only, overall RouteCast objective remains active.')
if __name__=='__main__':main()
