"""One deterministic dependent owner; no producer recovery or resubmission."""
import pathlib,json,hashlib,time,subprocess,sys,resource
R=pathlib.Path(__file__).resolve().parents[1]
def identity(pid):
 try:s=pathlib.Path(f'/proc/{pid}/stat').read_text()
 except FileNotFoundError:return None
 return int(s[s.rfind(')')+2:].split()[19])
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
def limits():resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
def main():
 pid,ticks=map(int,sys.argv[1:]);assert identity(pid)==ticks;M=R/'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19';O=R/'experiments/mmc_full_ensemble_checks_v1_2026-10-19';O.mkdir();scripts=['audit_MMC_full_NET_tree_ensemble_v1_2026_10_19.py','evaluate_MMC_full_NET_tree_ensemble_v1_2026_10_19.py'];files=[pathlib.Path(__file__).resolve(),M/'protocol.json',*(R/'tools'/s for s in scripts),R/'tools/prospective_pressure_metrics_v1.py'];bindings={str(p):sha(p) for p in files};write(O/'protocol.json',dict(bindings=bindings,producer_pid=pid,producer_start_ticks=ticks,commands=[[sys.executable,str(R/'tools'/s)] for s in scripts],poll_seconds=30,producer_restart=False,scope='Deterministic downstream full prediction audit and fixed known-data evaluation. No global goal completion or automatic promotion. Independent final metric verification remains pending.'));print('WAITING EXACT PRODUCER',pid,ticks,flush=True)
 while identity(pid)==ticks:time.sleep(30)
 receipt=M/'receipt.json'
 if not receipt.exists() or json.loads(receipt.read_text())['status']!='ALL3_COMPLETE_55300_NET_ENSEMBLE_PREDICTIONS_PRODUCED':
  write(O/'terminal.json',dict(status='PRODUCER_FAILED_OR_UNPROVEN'));raise SystemExit(1)
 rows=[]
 for i,s in enumerate(scripts,1):
  for p,h in bindings.items():assert sha(p)==h,p
  print('DOWNSTREAM START',s,flush=True)
  with (O/f'stage_{i}.log').open('x') as f:code=subprocess.run([sys.executable,str(R/'tools'/s)],cwd=R,stdout=f,stderr=subprocess.STDOUT,preexec_fn=limits).returncode
  row=dict(script=s,exit_code=code);rows.append(row);write(O/f'stage_{i}_terminal.json',row)
  if code:write(O/'terminal.json',dict(status='DOWNSTREAM_FAILED',rows=rows));raise SystemExit(code)
 write(O/'terminal.json',dict(status='FULL_PREDICTION_AUDIT_AND_DEVELOPMENT_EVALUATION_COMPLETE',rows=rows,independent_metric_verification_pending=True,goal_complete=False));print('DOWNSTREAM COMPLETE',flush=True)
if __name__=='__main__':main()
