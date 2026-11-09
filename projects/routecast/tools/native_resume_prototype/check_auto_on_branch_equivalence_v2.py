"""All24 same-input AUTO reruns at fanout0 vs frozen ON outputs."""
import json,os,shutil,subprocess,sys,time
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
from native_route_work_metrics import extract
ROOT=Path(__file__).resolve().parents[2];prior=ROOT/'experiments/native_resume_allfanout_cohort_2026-10-07/verification.json'
e=json.loads(prior.read_text());assert all(sha(p)==h for p,h in e['bindings'].items())
out=ROOT/'experiments/native_resume_auto_on_equivalence_v2_2026-10-07';out.mkdir(exist_ok=False)
bindings={str(prior):sha(prior),str(Path(__file__)):sha(Path(__file__)),str(ROOT/'tools/native_route_ledger_import_compact.py'):sha(ROOT/'tools/native_route_ledger_import_compact.py'),str(ROOT/'tools/native_route_work_metrics.py'):sha(ROOT/'tools/native_route_work_metrics.py')}
up=ROOT.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vpr/src'
for file in (up/'route/route.cpp',up/'base/read_options.cpp',ROOT/'build/native_resume_target_partial_v7_2026-10-07/source/route.cpp'):bindings[str(file)]=sha(file)
rows=[];tasks=[]
for case in e['rows']:
 assert case['complete']
 for mode in ('workflow','cold'):
  w,i=case['width'],case['index'];base=ROOT/f'experiments/native_resume_allfanout_w{w}_m{i}_{mode}_2026-10-07'
  receipt=json.loads((base/'receipt.json').read_text());p=json.loads((base/'protocol.json').read_text());assert receipt['protocol_sha256']==sha(base/'protocol.json')
  native=next(s['native'] for s in receipt['stages'] if 'native' in s)
  cmd=list(native['command']);assert cmd[cmd.index('--min_incremental_reroute_fanout')+1]=='0' and cmd[cmd.index('--incremental_reroute_delay_ripup')+1]=='on'
  cmd[cmd.index('--incremental_reroute_delay_ripup')+1]='auto'
  assert '--congested_routing_iteration_threshold' not in cmd and cmd[cmd.index('--max_router_iterations')+1]=='100'
  source=ROOT/f'work/mux_crossbar_channel_pressure_2026-10-06/mux_w{w}_c128'
  targets=[(source/'design.blif','design.blif'),(Path(next(f for f in p['inputs'] if f.endswith('/design.net'))),'design.net'),(Path(next(f for f in p['inputs'] if f.endswith('/target.place'))),'design.place')]
  for file,name in targets:assert sha(file)==p['inputs'][str(file)];bindings[str(file)]=sha(file)
  for file in (base/'receipt.json',base/'protocol.json',base/'first/run.log',base/'first/output.route'):bindings[str(file)]=sha(file)
  tasks.append(dict(width=w,index=i,mode=mode,base=str(base),command=cmd,files=[(str(f),name) for f,name in targets]))
(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,tasks=tasks,scope='All24 fixed fanout0, only ON->AUTO native rerun; expected equivalence because NORMAL persists before iteration100. No new full pipeline timing; source/route/proof hashes bound. Failure retained and not silently skipped.'),indent=2)+'\n')
norm=lambda f:{name:Counter(ps) for name,ps in physical_paths(f).items() if ps}
for task in tasks:
 w,i,mode=task['width'],task['index'],task['mode'];work=out/f'w{w}_m{i}_{mode}';work.mkdir();base=Path(task['base'])
 for file,name in task['files']:shutil.copyfile(file,work/name)
 env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
 if mode=='workflow':env.update(ROUTECAST_RESUME_SAME_PLACE_ROUTE=str(base/'first_seed.route'),ROUTECAST_RESUME_ALLOW_PARTIAL='1')
 with (work/'run.log').open('w') as stream:code=subprocess.run(task['command'],cwd=work,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=180).returncode
 row=dict(width=w,index=i,mode=mode,exit_code=code,files={str(f):sha(f) for f in work.iterdir() if f.is_file()})
 if code==0:
  metrics=extract((work/'run.log').read_text());oldmetrics=extract((base/'first/run.log').read_text())
  row.update(paths_equal=norm(work/'output.route')==norm(base/'first/output.route'),work_equal=all(metrics[k]==oldmetrics[k] for k in ('iterations','heap_pushes','rerouted_connection_attempts')),iterations=metrics['iterations'],rerouted_net_rows_equal=[r['rerouted_nets'] for r in metrics['iteration_rows']]==[r['rerouted_nets'] for r in oldmetrics['iteration_rows']])
  assert metrics['routing_success'] and metrics['native_vpr_succeeded']
 rows.append(row)
 (out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n');print(w,i,mode,code,row.get('paths_equal'),flush=True)
assert all(sha(p)==h for p,h in bindings.items())
assert len(rows)==24 and all(r['exit_code']==0 and r['paths_equal'] and r['work_equal'] and r['rerouted_net_rows_equal'] and r['iterations']<100 for r in rows)
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),all24_paths_and_work_equal=True,scope='AUTO and ON behavior same in these NORMAL-mode fanout0 native runs. FULL succeeds and route paths exactly reuse previous canonical/endpoint/capacity evidence, no new canonical execution. No equivalence for CONFLICTED, changed inputs or seeds. No cost-gain claim.'),indent=2)+'\n')
