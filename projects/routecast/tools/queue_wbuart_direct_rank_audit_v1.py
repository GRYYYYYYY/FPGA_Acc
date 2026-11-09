"""One audit owner per fold; observe the original PID, never restart training."""
import json,os,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];ep=sys.argv[1];pid=int(sys.argv[2]);D=R/'experiments/wbuart_direct_rank_tree_v1_2026-10-20'/ep;p=Path('/proc')/str(pid);start=(p/'stat').read_text().split()[21];assert b'fit_wbuart_direct_rank_tree_fold_v1.py' in (p/'cmdline').read_bytes();receipt=D/'audit_queue_v1.json';assert not receipt.exists();receipt.write_text(json.dumps({'status':'WAITING_ORIGINAL_FIT_PID','pid':pid,'proc_start_ticks':start,'queue_pid':os.getpid(),'episode':ep,'restart_allowed':False},indent=2)+'\n');print('AUDIT_QUEUE_WAITING',ep,pid,flush=True)
while True:
 try:
  stat=(p/'stat').read_text().split()
  if stat[21]!=start or stat[2]=='Z':break
 except FileNotFoundError:break
 time.sleep(20)
if not (D/'predictions_frozen.json').exists():
 receipt.write_text(json.dumps({'status':'STOPPED_FIT_TERMINAL_WITHOUT_FROZEN_OUTPUT','pid':pid,'queue_pid':os.getpid(),'episode':ep},indent=2)+'\n');raise SystemExit(2)
receipt.write_text(json.dumps({'status':'AUDIT_RUNNING','pid':pid,'queue_pid':os.getpid(),'episode':ep},indent=2)+'\n');print('AUDIT_QUEUE_START_REBUILD',ep,flush=True);code=subprocess.call([sys.executable,'-u',str(R/'tools/verify_wbuart_direct_rank_tree_fold_v1.py'),ep],cwd=R);receipt.write_text(json.dumps({'status':'AUDIT_PASS' if code==0 else 'AUDIT_FAILED','returncode':code,'pid':pid,'queue_pid':os.getpid(),'episode':ep},indent=2)+'\n');raise SystemExit(code)
