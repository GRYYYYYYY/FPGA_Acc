"""Single downstream owner; wait for exact native coordinator then run frozen checks."""
import pathlib,json,hashlib,subprocess,sys,time,os,resource
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
def identity(pid):
 try:s=pathlib.Path(f'/proc/{pid}/stat').read_text()
 except FileNotFoundError:return None
 return int(s[s.rfind(')')+2:].split()[19])
def limits():resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
def main():
 pid,ticks=map(int,sys.argv[1:]);assert identity(pid)==ticks
 P=R/'experiments/mmc_prospective_pressure_protocol_v2_2026-10-19';freeze=P/'evaluation_code_freeze_v1.json';frozen=json.loads(freeze.read_text());N=R/'experiments/mmc_prospective_pressure_native_v2_2026-10-19';O=R/'experiments/mmc_prospective_pressure_pipeline_v2_2026-10-19';O.mkdir()
 names=['verify_MMC_prospective_pressure_traces_v2_2026_10_19.py','extract_MMC_prospective_pressure_targets_v2_2026_10_19.py','evaluate_MMC_prospective_pressure_v2_2026_10_19.py'];commands=[[sys.executable,str(R/'tools'/n)] for n in names]
 bindings={str(freeze):sha(freeze),str(pathlib.Path(__file__).resolve()):sha(__file__),**frozen['bindings']}
 for p,h in bindings.items():assert sha(p)==h,p
 write(O/'protocol.json',dict(bindings=bindings,upstream_pid=pid,upstream_start_ticks=ticks,commands=commands,poll_seconds=30,restart_native=False,scope='Deterministic downstream checks only; never recover/restart native runs. Success is forecast evaluation completion, not full research goal completion.'))
 print('WAIT FOR EXACT NATIVE COORDINATOR',pid,ticks,flush=True)
 while identity(pid)==ticks:time.sleep(30)
 terminal=N/'terminal.json'
 if not terminal.exists() or json.loads(terminal.read_text())['status']!='THREE_NATIVE_PHYSICAL_CANONICAL_PASS':
  write(O/'terminal.json',dict(status='UPSTREAM_FAILED_OR_UNPROVEN',native_terminal_path=str(terminal)));raise SystemExit(1)
 rows=[]
 for index,cmd in enumerate(commands):
  for p,h in bindings.items():assert sha(p)==h,p
  print('DOWNSTREAM START',pathlib.Path(cmd[1]).name,flush=True)
  with (O/f'stage_{index+1}.log').open('x') as out:code=subprocess.run(cmd,cwd=R,stdout=out,stderr=subprocess.STDOUT,preexec_fn=limits).returncode
  row=dict(script=cmd[1],exit_code=code);rows.append(row);write(O/f'stage_{index+1}_terminal.json',row)
  if code:write(O/'terminal.json',dict(status='DOWNSTREAM_FAILED',rows=rows));raise SystemExit(code)
 write(O/'terminal.json',dict(status='FROZEN_TRACE_TARGET_AND_FORECAST_PIPELINE_COMPLETE',rows=rows,complete_research_goal=False));print('ALL DOWNSTREAM CHECKS COMPLETE',flush=True)
if __name__=='__main__':main()
