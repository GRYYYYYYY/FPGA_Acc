"""All18 unabridged source-context arm/case physical and event audits."""
import concurrent.futures,json,subprocess,sys,time,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure

def main():
 root=R/'experiments/mmc_source_context_ablation_v1_2026-10-18';r=json.loads((root/'results.json').read_text());assert r['status']=='all9_source_input_ablation_models_complete_audits_pending' and len(r['cases'])==9;out=root/'independent_audits';out.mkdir(exist_ok=False);tasks=[];reused=[];reuse_bindings={}
 for row in r['cases']:
  case,arm=row['case'],row['arm'];model=root/case/arm
  early=root/'early_model_audits'/case/arm;controller=early/'controller.json'
  if controller.exists():
   while True:
    c=json.loads(controller.read_text());assert c['case']==case and c['arm']==arm
    if c['status']=='complete':break
    assert c['status']=='running',('early audit failed; no duplicate run',case,arm)
    try:
     st=Path(f"/proc/{c['pid']}/stat").read_text().rsplit(')',1)[1].split();live=st[0]!='Z' and st[19]==c['startticks']
    except FileNotFoundError:live=False
    if not live:
     if json.loads(controller.read_text())['status']=='complete':continue
     raise RuntimeError(('early model auditor terminal without completion; no restart',case,arm))
    time.sleep(5)
   vp=early/'verification.json';v=json.loads(vp.read_text());assert sha(vp)==c['verification_sha256'] and v['case']==case and v['arm']==arm and v['complete_frame_and_all_events_pass'];assert all(sha(k)==h for k,h in v['bindings'].items());reuse_bindings[str(vp)]=sha(vp);reuse_bindings[str(controller)]=sha(controller)
   for kind in ['frame','events']:
    source=early/f'{kind}.json';assert v['bindings'][str(source)]==sha(source);dest=out/f'{case}_{arm}_{kind}.json';shutil.copyfile(source,dest);assert sha(source)==sha(dest);reuse_bindings[str(source)]=sha(source);reused.append(dict(case=case,arm=arm,kind=kind,exit_code=0,reused_from=str(source)));print('SOURCE_CONTEXT_AUDIT_REUSED',case,arm,kind,flush=True)
   continue
  for kind,script,arg in [('frame','verify_native_endpoint_v2_feedback_frame_v1_2026_10_18.py','sketch'),('events','verify_source_context_feedback_events_v1_2026_10_18.py','mmc')]:tasks.append((case,arm,kind,[sys.executable,str(R/'tools'/script),str(model),arg,str(out/f'{case}_{arm}_{kind}.json')]))
 def run(t):
  case,arm,kind,cmd=t
  with (out/f'{case}_{arm}_{kind}.log').open('x') as log:code=subprocess.call(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT)
  print('SOURCE_CONTEXT_AUDIT',case,arm,kind,code,flush=True);return dict(case=case,arm=arm,kind=kind,exit_code=code)
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=reused+list(pool.map(run,tasks))
 bindings={**closure([Path(__file__)]),**reuse_bindings,str(root/'results.json'):sha(root/'results.json')}
 for row in rows:
  if row['exit_code']==0:
   p=out/f"{row['case']}_{row['arm']}_{row['kind']}.json";v=json.loads(p.read_text());assert all(sha(k)==h for k,h in v['bindings'].items());bindings[str(p)]=sha(p)
 passed=len(rows)==18 and all(x['exit_code']==0 for x in rows);(out/'verification.json').write_text(json.dumps(dict(status='pass' if passed else 'failed',all9_full_frames_and_source_context_event_replays_pass=passed,bindings=bindings,rows=rows),indent=2));assert passed
if __name__=='__main__':main()
