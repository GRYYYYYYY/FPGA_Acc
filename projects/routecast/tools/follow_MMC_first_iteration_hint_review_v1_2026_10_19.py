"""Single deterministic downstream owner: wait exact cohort, replay, compare frozen gates."""
import pathlib,json,hashlib,subprocess,sys,time,os
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def identity(pid):
 try:s=pathlib.Path(f'/proc/{pid}/stat').read_text()
 except FileNotFoundError:return None
 return s.rsplit(')',1)[1].split()[19]
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def main():
 pid=int(sys.argv[1]);ticks=sys.argv[2];assert identity(pid)==ticks;O=R/'experiments/mmc_first_iteration_hint_review_chain_v1_2026-10-19';O.mkdir(exist_ok=False);N=R/'experiments/mmc_first_iteration_hint_utility_v1_2026-10-19';terminal=N/'terminal.json';scripts=[R/'tools/verify_MMC_first_iteration_hint_traces_v1_2026_10_19.py',R/'tools/compare_MMC_first_iteration_hint_utility_v1_2026_10_19.py'];files=[*scripts,pathlib.Path(__file__).resolve(),R/'tools/native_owner_trace_replay_v1.py',R/'experiments/mmc_first_iteration_hint_utility_protocol_v1_2026-10-19/protocol.json'];bindings={str(p):sha(p) for p in files};write(O/'protocol.json',dict(bindings=bindings,upstream_pid=pid,upstream_startticks=ticks,poll_seconds=20,restart_or_recover_any_job=False,actions=['Wait exact native owner and require authoritative all6 terminal receipt.','Run fixed independent full trace replay and actual expiry-bit checks.','Run unchanged all-case native component comparisons.'],scientific_interpretation_owner='Current main thread; deterministic checker only, no model substitution or policy tuning.'));write(O/'live_process.json',dict(pid=os.getpid(),startticks=identity(os.getpid())));print('WAIT_EXACT_FIRST_HINT_COHORT',pid,ticks,flush=True)
 while identity(pid)==ticks:time.sleep(20)
 if not terminal.exists():write(O/'terminal.json',dict(status='UPSTREAM_EXITED_WITHOUT_AUTHORITATIVE_TERMINAL_NO_RESTART'));return
 native=json.loads(terminal.read_text())
 if native['status']!='ALL6_NATIVE_READBACK_PHYSICAL_CANONICAL_PASS':write(O/'terminal.json',dict(status='UPSTREAM_FAILURES_PRESERVED_MAIN_ANALYSIS_REQUIRED',upstream_terminal=str(terminal),upstream_status=native['status']));return
 for p,h in bindings.items():assert sha(pathlib.Path(p))==h
 stages=[]
 for name,script in zip(['independent_trace_replay','native_component_comparison'],scripts):
  print('FIRST_HINT_REVIEW_START',name,flush=True)
  with (O/(name+'.log')).open('x') as log:
   child=subprocess.Popen([sys.executable,str(script)],cwd=R,stdout=log,stderr=subprocess.STDOUT);write(O/'live_stage.json',dict(stage=name,pid=child.pid,startticks=identity(child.pid)));code=child.wait()
  stages.append(dict(stage=name,exit_code=code));write(O/'stages.json',stages);print('FIRST_HINT_REVIEW_TERMINAL',name,code,flush=True)
  if code:write(O/'terminal.json',dict(status='DETERMINISTIC_AUDIT_FAILED_MAIN_ANALYSIS_REQUIRED',stages=stages));return
 result=R/'experiments/mmc_first_iteration_hint_utility_review_v1_2026-10-19/research_decision_v1.json';assert result.exists();write(O/'terminal.json',dict(status='ALL6_NATIVE_REPLAY_AND_FROZEN_COMPONENT_COMPARISON_COMPLETE',stages=stages,decision=str(result),decision_sha256=sha(result),scientific_interpretation_pending=True,full_research_goal_complete=False))
if __name__=='__main__':main()
