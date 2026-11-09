"""Independent full original-XML frame and event replay for owner scheduling."""
import concurrent.futures,json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure

def main():
 root=R/'experiments/mmc_owner_expansion_feedback_v1_2026-10-18';assert json.loads((root/'results.json').read_text())['status']=='all3_candidate_feedback_complete_audits_pending'
 out=root/'independent_audits';out.mkdir(exist_ok=False);tasks=[]
 for case in ['case_01','case_02','case_03']:
  for kind,script,arg in [('frame','verify_native_endpoint_v2_feedback_frame_v1_2026_10_18.py','sketch'),('events','verify_owner_expansion_feedback_events_v1_2026_10_18.py','mmc')]:
   tasks.append((case,kind,[sys.executable,str(R/'tools'/script),str(root/case),arg,str(out/f'{case}_{kind}.json')]))
 def run(task):
  case,kind,cmd=task
  with (out/f'{case}_{kind}.log').open('x') as log:code=subprocess.call(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT)
  print('AUDIT_DONE',case,kind,code,flush=True);return dict(case=case,kind=kind,exit_code=code)
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(run,tasks))
 bindings={**closure([Path(__file__)]),str(root/'results.json'):sha(root/'results.json')}
 for row in rows:
  if row['exit_code']==0:
   p=out/f"{row['case']}_{row['kind']}.json";v=json.loads(p.read_text());assert all(sha(k)==h for k,h in v['bindings'].items());bindings[str(p)]=sha(p)
 passed=all(row['exit_code']==0 for row in rows)
 (out/'verification.json').write_text(json.dumps(dict(status='pass' if passed else 'failed',all3_full_frames_and_owner_expanded_event_replays_pass=passed,bindings=bindings,rows=rows),indent=2));assert passed
if __name__=='__main__':main()
