"""Diagnostic replay with all iteration routes; not a performance comparison."""
import json,sys,subprocess,os,shutil,time,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
C=R/'experiments/freecores_continuous_workflow_v1_2026-10-08';D=R/'experiments/freecores_native_iteration_capture_v1_2026-10-08';D.mkdir()
p=C/'verification.json';proof=json.loads(p.read_text());assert proof['all_cases_both_complete_arms_authenticated'] and all(sha(k)==h for k,h in proof['bindings'].items());diag=R/'experiments/freecores_native_trajectory_diagnosis_v1_2026-10-08/diagnosis.json';d=json.loads(diag.read_text());assert all(sha(k)==h for k,h in d['bindings'].items())
bindings={str(x):sha(x) for x in [Path(__file__),p,diag]};cases=[]
for name in ['8051','xtea']:
 for mode in ['cold','seed']:
  src=C/mode/'native'/name;rp=src/'receipt.json';receipt=json.loads(rp.read_text());assert all(sha(k)==h for group in ['bindings','files'] for k,h in receipt[group].items());bindings[str(rp)]=sha(rp);w=D/name/mode;w.mkdir(parents=True)
  for f in ['design.blif','design.net','design.place']:shutil.copyfile(src/f,w/f);bindings[str(src/f)]=sha(src/f)
  cmd=receipt['command']+['--save_routing_per_iteration','on'];bindings[cmd[0]]=sha(cmd[0]);bindings[cmd[1]]=sha(cmd[1]);graph=cmd[cmd.index('--read_rr_graph')+1];bindings[graph]=sha(graph);extra={}
  if mode=='seed':shutil.copyfile(src/'seed.route',w/'seed.route');bindings[str(src/'seed.route')]=sha(src/'seed.route');extra={'ROUTECAST_NATIVE_SEED':str(w/'seed.route')}
  cases.append(dict(name=name,mode=mode,command=cmd,environment=extra,original_receipt=str(rp)))
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,cases=cases,timeout_seconds=1200,scope='All four frozen fresh cases, same argv except save_routing_per_iteration on. Same exact seed and inputs. All iteration route files kept for physical node/NET conflict diagnosis. Serialization IO changes timings; no performance claim. No price/seed tuning or omitted failure.'),indent=2)+'\n');rows=[]
for case in cases:
 w=D/case['name']/case['mode'];tick=time.perf_counter()
 with (w/'native.log').open('w') as f:
  try:code=subprocess.run(case['command'],cwd=w,env={**{k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')},**case['environment']},stdout=f,stderr=subprocess.STDOUT,timeout=1200).returncode
  except subprocess.TimeoutExpired:code='TIMEOUT'
 row=dict(name=case['name'],mode=case['mode'],exit_code=code,diagnostic_capture_seconds=time.perf_counter()-tick,status='FAILED_OR_TIMEOUT')
 try:
  log=(w/'native.log').read_text();assert code==0 and 'VPR succeeded' in log;n=int(re.search(r'Successfully routed after (\d+) routing iterations',log)[1]);files=sorted(w.glob('iteration_*.route'));assert [x.name for x in files]==[f'iteration_{i:03d}.route' for i in range(1,n+1)];baseline=next(x for x in d['rows'] if x['name']==case['name'])['cohorts']['fresh'][case['mode']]['records'];pattern=re.compile(r'^\s*(\d+)\s+[\d.]+\s+[\d.]+\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+\(\s*[\d.]+%\)\s+(\d+)\s+\(');observed=[list(map(int,m.groups())) for line in log.splitlines() if (m:=pattern.match(line))];keys=['iteration','bb_updates','heap_pushes','nets_routed','connections_routed','overused_node_count','wirelength'];assert observed==[[r[k] for k in keys] for r in baseline];row.update(status='ALL_ITERATIONS_CAPTURED_DISCRETE_TRAJECTORY_MATCH',iterations=n)
 except Exception as error:row['error']=repr(error)
 row['files']={str(x):sha(x) for x in w.iterdir() if x.is_file()};rows.append(row);(D/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(row['name'],row['mode'],row['status'],row.get('error'),flush=True)
assert all(sha(k)==h for k,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows),indent=2)+'\n')
