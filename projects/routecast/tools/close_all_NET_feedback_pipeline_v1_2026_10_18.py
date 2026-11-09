"""Follow one owned pipeline, then summarize and apply unchanged original gates."""
import json,os,subprocess,sys,time,datetime
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
root=R/'experiments/mmc_all_NET_feedback_v1_2026-10-18';pid=int(sys.argv[1]);ticks=sys.argv[2]
def live():
 try:
  s=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split();return s[0]!='Z' and s[19]==ticks
 except FileNotFoundError:return False
assert live();receipt=root/'postprocessing_supervision.json';assert not receipt.exists();scripts=[R/'tools/summarize_all_NET_feedback_v1_2026_10_18.py',R/'tools/finalize_all_NET_feedback_candidate_v1_2026_10_18.py'];bindings=closure([Path(__file__),*scripts])
def record(status,**kw):
 d=dict(status=status,bindings=bindings,pipeline_pid=pid,pipeline_startticks=ticks,updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**kw);tmp=receipt.with_suffix('.tmp');tmp.write_text(json.dumps(d,indent=2));os.replace(tmp,receipt)
def state():return json.loads((root/'pipeline_supervision.json').read_text())['status']
record('waiting_for_owned_audit_quality_pipeline')
while True:
 status=state()
 if status=='candidate_audits_and_original_quality_evaluation_complete':break
 if status=='failed':record('pipeline_failed_no_postprocessing_no_restart');raise SystemExit(1)
 if not live():
  if state()=='candidate_audits_and_original_quality_evaluation_complete':break
  record('pipeline_terminal_without_completion_no_restart');raise SystemExit(1)
 time.sleep(10)
for script in scripts:
 assert all(sha(k)==h for k,h in bindings.items());record('running_postprocessing',script=str(script));print('POSTPROCESS',script.name,flush=True)
 with (root/f'{script.stem}.log').open('x') as log:code=subprocess.call([sys.executable,str(script)],cwd=R,stdout=log,stderr=subprocess.STDOUT)
 if code:record('postprocessing_failed',script=str(script),exit_code=code);raise SystemExit(code)
record('all_NET_candidate_review_complete_original_gate_decision_recorded');print('POSTPROCESS COMPLETE',flush=True)
