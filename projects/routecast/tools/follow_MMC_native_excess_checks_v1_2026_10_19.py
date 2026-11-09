"""Single downstream owner for fixed native preload experiment; never restart it."""
import pathlib,json,hashlib,subprocess,sys,time,resource
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
 pid,ticks=map(int,sys.argv[1:]);assert identity(pid)==ticks;N=R/'experiments/mmc_native_excess_utility_v1_2026-10-19';P=R/'experiments/mmc_native_excess_utility_protocol_v1_2026-10-19/protocol.json';O=R/'experiments/mmc_native_excess_checks_v1_2026-10-19';O.mkdir();scripts=['verify_MMC_native_excess_traces_v1_2026_10_19.py','compare_MMC_native_excess_utility_v1_2026_10_19.py'];files=[P,pathlib.Path(__file__).resolve(),*(R/'tools'/s for s in scripts),R/'tools/native_owner_trace_replay_v1.py'];bindings={str(p):sha(p) for p in files};write(O/'protocol.json',dict(bindings=bindings,upstream_pid=pid,upstream_start_ticks=ticks,commands=[[sys.executable,str(R/'tools'/s)] for s in scripts],poll_seconds=30,restart_native=False,scope='Independent replay and frozen native component utility gate only; no full research completion or automatic promotion.'));print('WAITING EXACT NATIVE COORDINATOR',pid,ticks,flush=True)
 while identity(pid)==ticks:time.sleep(30)
 terminal=N/'terminal.json'
 if not terminal.exists() or json.loads(terminal.read_text())['status']!='ALL6_NATIVE_READBACK_PHYSICAL_CANONICAL_PASS':write(O/'terminal.json',dict(status='UPSTREAM_FAILED_OR_UNPROVEN',native_terminal=str(terminal),no_native_utility_admission=True));raise SystemExit(1)
 rows=[]
 for i,s in enumerate(scripts,1):
  for p,h in bindings.items():assert sha(p)==h,p
  print('NATIVE DOWNSTREAM START',s,flush=True)
  with (O/f'stage_{i}.log').open('x') as f:code=subprocess.run([sys.executable,str(R/'tools'/s)],cwd=R,stdout=f,stderr=subprocess.STDOUT,preexec_fn=limits).returncode
  row=dict(script=s,exit_code=code);rows.append(row);write(O/f'stage_{i}_terminal.json',row)
  if code:write(O/'terminal.json',dict(status='DOWNSTREAM_FAILED',rows=rows));raise SystemExit(code)
 write(O/'terminal.json',dict(status='SIX_NATIVE_TRACES_REPLAYED_AND_FIXED_COMPONENT_DECISION_SAVED',rows=rows,complete_workflow_gain_proven=False,goal_complete=False));print('NATIVE COMPONENT REVIEW COMPLETE',flush=True)
if __name__=='__main__':main()
