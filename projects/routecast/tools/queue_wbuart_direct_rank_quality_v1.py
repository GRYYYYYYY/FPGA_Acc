"""Single downstream owner, fail closed on a dead or failed audit queue."""
import json,os,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/wbuart_direct_rank_tree_v1_2026-10-20';receipt=D/'quality_queue_v1.json';assert not receipt.exists();records=[]
for ep in ['episode_01','episode_02','episode_03']:
 p=D/ep/'audit_queue_v1.json';q=json.loads(p.read_text());pid=q['queue_pid'];proc=Path('/proc')/str(pid);assert b'queue_wbuart_direct_rank_audit_v1.py' in (proc/'cmdline').read_bytes();records.append((ep,p,pid,(proc/'stat').read_text().split()[21]))
def save(state,**extra):receipt.write_text(json.dumps({'status':state,'queue_pid':os.getpid(),'audit_queue_pids':[r[2] for r in records],**extra},indent=2)+'\n')
save('WAITING_ALL3_AUDITS');print('QUALITY_QUEUE_WAITING_ALL3_AUDITS',flush=True)
while True:
 ready=0
 for ep,p,pid,start in records:
  q=json.loads(p.read_text())
  if q['status']=='AUDIT_PASS':
   assert q['returncode']==0 and (D/ep/'independent_verification_v1.json').exists();ready+=1;continue
  if q['status'] in ['AUDIT_FAILED','STOPPED_FIT_TERMINAL_WITHOUT_FROZEN_OUTPUT']:save('STOPPED_UPSTREAM_FAILURE',episode=ep,upstream=q['status']);raise SystemExit(2)
  try:
   stat=(Path('/proc')/str(pid)/'stat').read_text().split();live=stat[21]==start and stat[2]!='Z'
  except FileNotFoundError:live=False
  if not live:save('STOPPED_AUDIT_QUEUE_TERMINAL_WITHOUT_PASS',episode=ep);raise SystemExit(3)
 if ready==3:break
 time.sleep(20)
save('QUALITY_RUNNING');print('QUALITY_QUEUE_START_ALL9',flush=True);code=subprocess.call([sys.executable,'-u',str(R/'tools/evaluate_wbuart_direct_rank_tree_v1.py')],cwd=R);save('QUALITY_FINISHED' if code==0 else 'QUALITY_FAILED',returncode=code);raise SystemExit(code)
