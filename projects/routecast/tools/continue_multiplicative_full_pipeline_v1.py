"""Wait exact original model wrapper; audit full new trajectory before frozen metrics."""
import json,sys,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from source_binding_v2 import closure
from pre_route_endpoints import sha
O=R/'experiments/mmc_multiplicative_feedback_trial_v1_2026-10-10';terminal=O/'model_terminal.json'
bindings=closure([Path(__file__),R/'tools/run_full_multiplicative_feedback_audits_v1.py',R/'tools/evaluate_mmc_multiplicative_hotspots_v1.py'])
(O/'pipeline_startup_v1.json').write_text(json.dumps(dict(bindings=bindings,model_wrapper_pid=2763738),indent=2)+'\n')
missing=0
while not terminal.exists():
 missing=0 if Path('/proc/2763738/cmdline').exists() else missing+1
 if missing>=3:raise RuntimeError('model wrapper missing without terminal evidence')
 time.sleep(5)
assert json.loads(terminal.read_text())['exit_status']==0
for name,script in [('audits','run_full_multiplicative_feedback_audits_v1.py'),('metrics','evaluate_mmc_multiplicative_hotspots_v1.py')]:
 assert all(sha(p)==h for p,h in bindings.items());print('PIPELINE START',name,flush=True)
 args=[sys.executable,str(R/'tools'/script)]+([str(O)] if name=='audits' else [])
 with (O/(name+'.log')).open('w') as f:code=subprocess.call(args,cwd=R,stdout=f,stderr=subprocess.STDOUT)
 (O/(name+'_terminal.json')).write_text(json.dumps(dict(exit_status=code),indent=2)+'\n')
 if code:raise SystemExit(code)
print('MULTIPLICATIVE AUDITS AND METRICS COMPLETE',flush=True)
