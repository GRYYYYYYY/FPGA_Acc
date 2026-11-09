"""Audit one terminal model case while later cases run; certificates are reusable."""
import concurrent.futures,datetime,json,os,subprocess,sys,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure

def main():
 case=sys.argv[1];assert case in ['case_01','case_02','case_03'];root=R/'experiments/mmc_all_NET_feedback_v1_2026-10-18';model=root/case;protocol=json.loads((model/'protocol.json').read_text());receipt=json.loads((model/'receipt.json').read_text());assert protocol['scheduling_policy']=='all_NETs_each_round';assert len(receipt['rounds'])==2 and all(len(r['events'])==len(r['affected_nets'])==55300 for r in receipt['rounds']);out=root/'early_case_audits'/case;out.mkdir(parents=True,exist_ok=False);stat=Path(f'/proc/{os.getpid()}/stat').read_text().rsplit(')',1)[1].split();identity=dict(pid=os.getpid(),startticks=stat[19],case=case)
 def record(status,**kw):
  p=out/'controller.json';tmp=out/'controller.tmp';tmp.write_text(json.dumps(dict(**identity,status=status,updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**kw),indent=2));os.replace(tmp,p)
 record('running')
 try:
  def run(task):
   kind,script,arg=task;cmd=[sys.executable,str(R/'tools'/script),str(model),arg,str(out/f'{kind}.json')]
   with (out/f'{kind}.log').open('x') as log:code=subprocess.call(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT)
   print('EARLY_AUDIT',case,kind,code,flush=True);return dict(case=case,kind=kind,exit_code=code)
  tasks=[('frame','verify_native_endpoint_v2_feedback_frame_v1_2026_10_18.py','sketch'),('events','verify_native_endpoint_v2_feedback_events_v1_2026_10_18.py','mmc')]
  with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(run,tasks))
  bindings={**closure([Path(__file__)]),str(model/'receipt.json'):sha(model/'receipt.json')};passed=all(r['exit_code']==0 for r in rows)
  for row in rows:
   if row['exit_code']==0:
    p=out/f"{row['kind']}.json";v=json.loads(p.read_text());assert all(sha(k)==h for k,h in v['bindings'].items());bindings[str(p)]=sha(p)
    if row['kind']=='events':assert v['events']==110600
  verification=out/'verification.json';verification.write_text(json.dumps(dict(status='pass' if passed else 'failed',bindings=bindings,case=case,rows=rows,complete_frame_and_all110600_events_pass=passed),indent=2));record('complete' if passed else 'failed',verification=str(verification),verification_sha256=sha(verification));assert passed
 except Exception:
  (out/'failure.txt').write_text(traceback.format_exc());record('failed');raise
if __name__=='__main__':main()
