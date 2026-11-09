"""Own one complete criticality feedback model process; audits remain required."""
import json,subprocess,sys,time
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];P=R/'experiments/criticality_feedback_driver_qualification_v1_2026-10-10/verification.json';proof=json.loads(P.read_text());assert all(sha(p)==h for p,h in proof['bindings'].items())
O=R/'experiments/mmc_full_criticality_feedback_trial_v1_2026-10-10';O.mkdir()
endpoint=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/demand/mmc/endpoints.json';driver=R/'tools/run_criticality_present_overflow_guard_model_v1.py';bindings={**proof['bindings'],str(P):sha(P),str(endpoint):sha(endpoint),str(Path(__file__).resolve()):sha(Path(__file__))}
command=[sys.executable,str(driver),str(endpoint),str(O/'model')];(O/'startup.json').write_text(json.dumps(dict(bindings=bindings,command=command,scope='Complete all115572 query new two-round feedback. Model only until required independent audits finish.'),indent=2)+'\n')
begin=time.perf_counter()
with (O/'model.log').open('w') as log:status=subprocess.run(command,cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
(O/'model_terminal.json').write_text(json.dumps(dict(exit_status=status,model_process_seconds=time.perf_counter()-begin,independent_new_trajectory_audits_complete=False),indent=2)+'\n');print('FULL CRITICALITY MODEL TERMINAL',status,flush=True)
if status:raise SystemExit(status)
