"""Execute all preregistered development outcomes, never select favorable cases."""
import sys,json,subprocess,time,os
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
P=R/'experiments/freecores_segment_delay_pool_downstream_prereg_v1_2026-10-08/protocol.json';p=json.loads(P.read_text());assert all(sha(k)==h for k,h in p['bindings'].items());OUT=R/'experiments/freecores_segment_delay_pool_downstream_v1_2026-10-08';OUT.mkdir();bindings={str(P):sha(P),str(Path(__file__)):sha(Path(__file__)),**p['bindings']};source=R/'experiments/freecores_segment_delay_pool_model_v1_2026-10-08/receipt.json';r=json.loads(source.read_text());assert all(sha(k)==h for k,h in r['bindings'].items()) and all(row['status']=='COMPLETE_INITIAL_FINAL_EVENT_AUDIT_PASS' and all(sha(k)==h for k,h in row['files'].items()) for row in r['rows']);assert [row['name'] for row in r['rows']]==p['cases'];bindings[str(source)]=sha(source)
commands=[]
for name in p['cases']:
 for tool in ['evaluate_freecores_segment_delay_pool_hotspots_v1.py','verify_freecores_segment_delay_pool_hotspots_v1.py']:commands.append([sys.executable,str(R/'tools'/tool),name])
commands.append([sys.executable,str(R/'tools/compare_freecores_segment_delay_pool_ablation_v1.py')])
for name in p['cases']:
 for tool in ['trial_freecores_segment_delay_pool_native_seed_v1.py','verify_freecores_segment_delay_pool_native_seed_v1.py']:commands.append([sys.executable,str(R/'tools'/tool),name])
for tool in ['trial_freecores_segment_delay_pool_seed_canonical_v1.py','verify_freecores_segment_delay_pool_seed_canonical_ignored_pins_v1.py']:commands.append([sys.executable,str(R/'tools'/tool)])
(OUT/'protocol.json').write_text(json.dumps(dict(bindings=bindings,commands=commands,timeout_per_stage_seconds=1200,scope=p['scope']),indent=2)+'\n');rows=[]
for i,cmd in enumerate(commands):
 tick=time.perf_counter();log=OUT/f'stage{i}.log'
 with log.open('w') as f:
  try:code=subprocess.run(cmd,cwd=R,env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')},stdout=f,stderr=subprocess.STDOUT,timeout=1200).returncode
  except subprocess.TimeoutExpired:code='TIMEOUT'
 rows.append(dict(stage=i,command=cmd,exit_code=code,component_seconds=time.perf_counter()-tick,log=str(log),log_sha256=sha(log)));(OUT/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(i,Path(cmd[1]).name,code,flush=True)
 if code!=0:break
assert all(sha(k)==h for k,h in bindings.items());(OUT/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,all_stages_terminal_zero=len(rows)==len(commands) and all(x['exit_code']==0 for x in rows),scope='Producer completion only; native/metric/canonical output and scientific admission remain separate. Component times not continuous full workflow.'),indent=2)+'\n')
