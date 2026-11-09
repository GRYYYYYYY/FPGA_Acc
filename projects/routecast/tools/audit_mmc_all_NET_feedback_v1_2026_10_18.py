"""Independent full original-XML frame and event replay for owner scheduling."""
import concurrent.futures,json,subprocess,sys,time,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure

def main():
 root=R/'experiments/mmc_all_NET_feedback_v1_2026-10-18';assert json.loads((root/'results.json').read_text())['status']=='all3_global_schedule_feedback_complete_independent_audits_pending'
 out=root/'independent_audits';out.mkdir(exist_ok=False);tasks=[];reused=[];reused_bindings={}
 for case in ['case_01','case_02','case_03']:
  protocol=json.loads((root/case/'protocol.json').read_text());receipt=json.loads((root/case/'receipt.json').read_text());assert protocol['scheduling_policy']=='all_NETs_each_round';assert all(len(rr['affected_nets'])==len(rr['events'])==55300 for rr in receipt['rounds'])
 for case in ['case_01','case_02','case_03']:
  early=root/'early_case_audits'/case;controller=early/'controller.json'
  if controller.exists():
   while True:
    c=json.loads(controller.read_text());assert c['case']==case and c['status'] in ['running','complete','failed']
    if c['status']=='complete':break
    assert c['status']!='failed',('early case audit failed; no duplicate rerun',case)
    try:
     st=Path(f"/proc/{c['pid']}/stat").read_text().rsplit(')',1)[1].split();live=st[0]!='Z' and st[19]==c['startticks']
    except FileNotFoundError:live=False
    if not live:
     if json.loads(controller.read_text())['status']=='complete':continue
     raise RuntimeError(('early audit terminal without certificate; no restart',case))
    time.sleep(5)
   vp=early/'verification.json';v=json.loads(vp.read_text());assert sha(vp)==c['verification_sha256'] and v['case']==case and v['complete_frame_and_all110600_events_pass'];assert all(sha(k)==h for k,h in v['bindings'].items());reused_bindings[str(vp)]=sha(vp);reused_bindings[str(controller)]=sha(controller)
   for kind in ['frame','events']:
    source=early/f'{kind}.json';assert v['bindings'][str(source)]==sha(source);dest=out/f'{case}_{kind}.json';shutil.copyfile(source,dest);assert sha(source)==sha(dest);reused.append(dict(case=case,kind=kind,exit_code=0,reused_from=str(source)));reused_bindings[str(source)]=sha(source);print('AUDIT_REUSED',case,kind,flush=True)
   continue
  for kind,script,arg in [('frame','verify_native_endpoint_v2_feedback_frame_v1_2026_10_18.py','sketch'),('events','verify_native_endpoint_v2_feedback_events_v1_2026_10_18.py','mmc')]:
   tasks.append((case,kind,[sys.executable,str(R/'tools'/script),str(root/case),arg,str(out/f'{case}_{kind}.json')]))
 def run(task):
  case,kind,cmd=task
  with (out/f'{case}_{kind}.log').open('x') as log:code=subprocess.call(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT)
  print('AUDIT_DONE',case,kind,code,flush=True);return dict(case=case,kind=kind,exit_code=code)
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=reused+list(pool.map(run,tasks))
 bindings={**closure([Path(__file__)]),**reused_bindings,str(root/'results.json'):sha(root/'results.json')}
 for row in rows:
  if row['exit_code']==0:
   p=out/f"{row['case']}_{row['kind']}.json";v=json.loads(p.read_text());assert all(sha(k)==h for k,h in v['bindings'].items());bindings[str(p)]=sha(p)
 passed=len(rows)==6 and all(row['exit_code']==0 for row in rows)
 (out/'verification.json').write_text(json.dumps(dict(status='pass' if passed else 'failed',all3_full_frames_and_all_NET_event_replays_pass=passed,bindings=bindings,rows=rows),indent=2));assert passed
if __name__=='__main__':main()
