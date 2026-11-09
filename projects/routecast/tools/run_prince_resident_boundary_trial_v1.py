"""Run fixed original full trajectories with snapshot output, retain every terminal."""
import json,subprocess,resource,shutil,os,time,re
from pathlib import Path
from pre_route_endpoints import sha
from replay_prince_native_sources_v1 import sequences
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_resident_boundary_trial_v1_2026-10-20'
PAT=re.compile(r'^\s*\d+\s+\d+\.\d+\s+\d+\.\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\(')
def limit():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
def table(p):return [line.split() for line in p.read_text().splitlines() if PAT.match(line)]
def main():
 pp=E/'prince_resident_boundary_trial_design_v1_2026-10-20/protocol.json';p=json.loads(pp.read_text());assert all(sha(f)==h for f,h in p['bindings'].items());D.mkdir(exist_ok=False);rows=[];start=time.perf_counter();env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
 for j in p['jobs']:
  d=Path(j['directory']);d.mkdir(parents=True);src=Path(j['source'])
  for name,f in j['staging'].items():shutil.copyfile(f,d/name);assert sha(f)==sha(d/name)
  env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
  if j['mode']=='capture':
   boundary=d/'boundary';boundary.mkdir();env['ROUTECAST_RESIDENT_BOUNDARY_DIR']=str(boundary)
  tick=time.perf_counter()
  with (d/'native.log').open('x') as log:code=subprocess.call(j['command'],cwd=d,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limit)
  shots=sorted(d.glob('iteration_*.route'));a=table(d/'native.log');b=table(src/'native.log');expected=[f'iteration_{i:03d}.route' for i in range(1,len(a)+1)];row=dict(case=j['case'],native_exit_code=code,native_seconds=time.perf_counter()-tick,iterations=len(a),all_iteration_snapshots_complete=[f.name for f in shots]==expected,all_iteration_summary_fields_match_except_clocks=[x[:1]+x[2:] for x in a]==[x[:1]+x[2:] for x in b],final_physical_sequences_identical=sequences(d/'output.route')==sequences(src/'output.route'),files={str(f):sha(f) for f in [d/'native.log',d/'output.route',*shots,*sorted((d/'boundary').glob('*'))]});(d/'receipt.json').write_text(json.dumps(row,indent=2)+'\n');rows.append(row);(D/'progress.json').write_text(json.dumps(dict(rows=rows),indent=2)+'\n');print('TRAJECTORY',j['case'],len(shots),row['final_physical_sequences_identical'],row['all_iteration_summary_fields_match_except_clocks'],flush=True)
 assert all(sha(f)==h for f,h in p['bindings'].items());(D/'verification.json').write_text(json.dumps(dict(rows=rows,bindings={str(pp):sha(pp),str(Path(__file__)):sha(__file__)},continuous_seconds=time.perf_counter()-start,scope='Complete snapshot capture with exact original terminal route and per-iteration summary comparison. Every physical snapshot still requires arc/endpoint/occupancy audit; no checkpoint quality selection or fullpaid gain.'),indent=2)+'\n')
if __name__=='__main__':main()
