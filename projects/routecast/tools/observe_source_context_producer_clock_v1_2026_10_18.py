"""Read-only original-process lifetime bracket including preflight and event output."""
import datetime,json,os,select,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
root=R/'experiments/mmc_source_context_ablation_v1_2026-10-18';pid=int(sys.argv[1]);ticks=int(sys.argv[2]);path=root/'producer_wall_clock_observation_v1.json';assert not path.exists()
def identity():
 try:
  s=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split();return s[0]!='Z' and int(s[19])==ticks
 except FileNotFoundError:return False
assert identity();fd=os.pidfd_open(pid);assert identity();poll=select.poll();poll.register(fd,select.POLLIN);assert not poll.poll(0);hz=os.sysconf('SC_CLK_TCK');tick_margin=1/hz;start=ticks/hz;clock=lambda:time.clock_gettime(time.CLOCK_BOOTTIME);bindings={**closure([Path(__file__)]),str(root/'protocol.json'):sha(root/'protocol.json')};base=dict(pid=pid,startticks=ticks,clock='CLOCK_BOOTTIME',kernel_start_tick_seconds=1/hz,start_time_estimate_seconds_since_boot=start,start_time_margin_seconds=tick_margin,bindings=bindings,scope='Entire original producer process: Python startup, input/code validation, shared graph loading, all case workspace/model calls, outputs and cleanup. Excludes future independent audit/quality/native/canonical phases. Not a matched full-workflow gain; no inference of producer exit status from pidfd. Start is read from original kernel process identity while live; no process injection or restart.')
def record(status,**kw):
 d=dict(**base,status=status,updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**kw);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(d,indent=2));os.replace(tmp,path)
record('observing_original_producer_lifetime',elapsed_when_observer_attached_seconds=clock()-start)
last_alive_before=clock()
while True:
 before=clock();events=poll.poll(1000);after=clock()
 if events:
  low=max(0,last_alive_before-(start+tick_margin));high=after-(start-tick_margin);result=root/'results.json';record('original_producer_terminal_observed',elapsed_wall_seconds_lower_bound=low,elapsed_wall_seconds_upper_bound=high,end_observation_interval_seconds=after-last_alive_before,complete_results_present=result.exists(),complete_results_sha256=sha(result) if result.exists() else None);print('ORIGINAL_PRODUCER_WALL_BRACKET',low,high,flush=True);break
 # A timeout confirms this exact pidfd was nonterminal through that poll;
 # use its BEFORE timestamp as a conservative live lower bound, including races.
 last_alive_before=before
os.close(fd)
