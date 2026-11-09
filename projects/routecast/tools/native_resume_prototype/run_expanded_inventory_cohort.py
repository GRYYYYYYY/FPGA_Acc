"""Frozen serial new-state cohort; retain every failure and outer elapsed time."""
import json,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from freeze_priority_family import closure
ROOT=Path(__file__).resolve().parents[2];out=ROOT/'experiments/native_resume_inventory_expanded_cohort_2026-10-07';out.mkdir(exist_ok=False);cases=[(8,3),(16,3),(32,0),(32,1)];producer=ROOT/'tools/native_resume_prototype/cohort_inventory_pipeline_trial.py';inputs={}
for w,i in cases:
 ep=ROOT/f'experiments/mux_budget_move_cohort_2026-10-06/w{w}_m{i}/target_endpoints.json';meta=json.loads(ep.read_text());inputs[str(ep)]=sha(ep)
 for x in meta['inputs'].values():inputs[x['path']]=x['sha256']
protocol=dict(cases=cases,inputs=inputs,sources=closure([Path(__file__),producer]),seed=1,max_router_iterations=100,timeout_each_seconds=300,policy='Unchanged all-NET exchange and single marking-pass native policy; penalty0.01ns, own worst-path first then original union-wire order, sink original-delay order. Same graph inventory initialization in workflow/cold. Fresh serial pairs; no changes from observed labels.',scope='New placement states within MUX family, not heldout-family validation. Continuous internal and outer subprocess elapsed measured, failed runs retained.')
assert all(sha(f)==h for f,h in {**inputs,**protocol['sources']}.items());(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');runs=[]
for w,i in cases:
 for mode in ('workflow','cold'):
  cmd=[sys.executable,str(producer),mode,str(w),str(i)];begin=time.perf_counter();log=out/f'w{w}_m{i}_{mode}.log'
  with log.open('w') as stream:
   try:code=subprocess.run(cmd,stdout=stream,stderr=subprocess.STDOUT,cwd=ROOT,timeout=300).returncode
   except subprocess.TimeoutExpired:code='timeout'
  row=dict(width=w,index=i,mode=mode,exit_code=code,outer_seconds=time.perf_counter()-begin,log_sha256=sha(log));runs.append(row);(out/'runs.json').write_text(json.dumps(runs,indent=2)+'\n');print(row,flush=True)
assert all(sha(f)==h for f,h in {**inputs,**protocol['sources']}.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),runs=runs),indent=2)+'\n')
