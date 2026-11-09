"""All9 native status callbacks, no iteration route output, paid diagnostics only."""
import json,subprocess,shutil,resource,time,os
from pathlib import Path
from pre_route_endpoints import sha
from run_prince_native_trajectory_v1 import table
from replay_prince_native_sources_v1 import sequences
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_status_consumer_trial_v1_2026-10-20'
def limit():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
def main():
 D.mkdir(exist_ok=False);oldp=E/'prince_native_trajectory_design_v1_2026-10-20/protocol.json';p=json.loads(oldp.read_text());build=R/'build/prince_resident_status_consumer_v1_2026-10-20';br=json.loads((build/'receipt.json').read_text());assert sha(build/'vpr')==br['binary_sha256'];jobs=[]
 for old in p['jobs']:
  for mode in ['digest','capture']:
   j=dict(old);j['mode']=mode;j['case']=old['case']+'/'+mode;j['directory']=str(D/j['case']);cmd=old['command'].copy();cmd[0]=str(build/'vpr');i=cmd.index('--save_routing_per_iteration');del cmd[i:i+2];j['command']=cmd;jobs.append(j)
 bindings={**p['bindings'],**{str(f):sha(f) for f in [oldp,build/'receipt.json',build/'protocol.json',build/'vpr',Path(__file__)]}};(D/'protocol.json').write_text(json.dumps(dict(jobs=jobs,bindings=bindings,policy='All9 fixed cases x digest/capture, unchanged native max100/seed1/worker1/termination. Save_routing_per_iteration absent. Original status function called once then const RR/box consumer runs in native stack; optional capture for parity only. No stop/restore/native mutation. Full process clocks include ledger writes; fixed unbalanced cases are not matched fullpaid speed evidence. FNV checksums are diagnostics, not cryptographic identity.'),indent=2)+'\n');rows=[];start=time.perf_counter()
 for j in jobs:
  tick=time.perf_counter();d=Path(j['directory']);d.mkdir(parents=True);src=Path(j['source'])
  for name,f in j['staging'].items():shutil.copyfile(f,d/name);assert sha(f)==sha(d/name)
  env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env['ROUTECAST_RESIDENT_CALLBACK_FILE']=str(d/'callback.tsv')
  if j['mode']=='capture':(d/'boundary').mkdir();env['ROUTECAST_RESIDENT_BOUNDARY_DIR']=str(d/'boundary')
  nt=time.perf_counter()
  with (d/'native.log').open('x') as log:code=subprocess.call(j['command'],cwd=d,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limit)
  native_seconds=time.perf_counter()-nt;a=table(d/'native.log');b=table(src/'native.log');assert not list(d.glob('iteration_*.route'));callbacks=(d/'callback.tsv').read_text().splitlines();row=dict(case=j['case'],native_exit_code=code,native_seconds=native_seconds,iterations=len(a),callback_rows=len(callbacks),callback_sequence_complete=[int(x.split()[0]) for x in callbacks]==list(range(1,len(a)+1)),no_iteration_route_files=True,nonclock_iteration_summaries_equal=[x[:1]+x[2:] for x in a]==[x[:1]+x[2:] for x in b],terminal_physical_sequences_equal=sequences(d/'output.route')==sequences(src/'output.route'),paid_case_seconds=time.perf_counter()-tick,files={str(f):sha(f) for f in [d/'native.log',d/'output.route',d/'callback.tsv',*sorted((d/'boundary').glob('*'))]});(d/'receipt.json').write_text(json.dumps(row,indent=2)+'\n');rows.append(row);(D/'progress.json').write_text(json.dumps(dict(rows=rows),indent=2)+'\n');print('STATUS_CONSUMER',j['case'],row['callback_sequence_complete'],row['nonclock_iteration_summaries_equal'],row['terminal_physical_sequences_equal'],flush=True)
 assert all(sha(f)==h for f,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(rows=rows,bindings={str(D/'protocol.json'):sha(D/'protocol.json'),str(Path(__file__)):sha(__file__)},continuous_seconds=time.perf_counter()-start,scope='Synchronous live read-only consumer without per-iteration route output; no stop, restart, full native state serialization or prediction policy.'),indent=2)+'\n')
if __name__=='__main__':main()
