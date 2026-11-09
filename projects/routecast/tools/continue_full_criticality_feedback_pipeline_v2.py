"""Wait for this exact owned model, then audit before metrics; never restart it."""
import json,sys,time,subprocess,os
from pathlib import Path
from pre_route_endpoints import sha
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/native_resume_prototype'))
from source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];O=R/'experiments/mmc_full_criticality_feedback_trial_v1_2026-10-10'
A=R/'tools/run_full_criticality_feedback_audits_v1.py';E=R/'tools/evaluate_mmc_criticality_hotspots_v1.py'
bindings=closure([Path(__file__),A,E]);bindings[str(O/'startup.json')]=sha(O/'startup.json')
assert not (O/'pipeline_receipt_v2.json').exists()
(O/'pipeline_startup_v2.json').write_text(json.dumps(dict(bindings=bindings,model_wrapper_pid=1444946,model_pid=1445036,scope='One exact existing model; require terminal0 then full audits before metric evaluation. No model restart.'),indent=2)+'\n')
stages=[];missing=0
while True:
 terminal=O/'model_terminal.json'
 if terminal.exists():
  try:result=json.loads(terminal.read_text())
  except json.JSONDecodeError:time.sleep(10);continue
  assert result['exit_status']==0,'Model failed; independent pipeline not started'
  break
 if Path('/proc/1444946/cmdline').exists():missing=0
 else:
  missing+=1
  if missing>=3:raise RuntimeError('Original model wrapper proc entry disappeared without terminal receipt; no restart')
 time.sleep(10)
assert all(sha(p)==h for p,h in bindings.items())
for name,command in [('audits',[sys.executable,str(A),str(O)]),('metrics',[sys.executable,str(E)])]:
 if name=='metrics':
  proof=json.loads((O/'independent_audits_verification.json').read_text());assert proof['all_three_full_audits_pass'] and all(sha(p)==h for p,h in proof['bindings'].items())
 start=time.perf_counter();print('PIPELINE START',name,flush=True)
 with (O/(name+'.log')).open('w') as log:status=subprocess.run(command,cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
 stages.append(dict(stage=name,command=command,exit_status=status,seconds=time.perf_counter()-start))
 (O/'pipeline_stages_v2.json').write_text(json.dumps(stages,indent=2)+'\n')
 if status:raise SystemExit(status)
 print('PIPELINE COMPLETE',name,flush=True)
assert all(sha(p)==h for p,h in bindings.items())
(O/'pipeline_receipt_v2.json').write_text(json.dumps(dict(bindings=bindings,stages=stages,scope='New complete model audit and exposed same-domain metrics only; native QoR/common end-to-end/heldout gates remain open.'),indent=2)+'\n')
