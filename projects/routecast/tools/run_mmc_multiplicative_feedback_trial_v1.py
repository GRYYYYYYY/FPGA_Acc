"""Bound full115572, two-round multiplicative control; terminal is not certification."""
import json,sys,time,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
O=R/'experiments/mmc_multiplicative_feedback_trial_v1_2026-10-10';O.mkdir(exist_ok=False)
bindings=closure([Path(__file__),R/'tools/run_criticality_multiplicative_guard_model_v1.py',R/'tools/verify_criticality_multiplicative_guard_events_v1.py'])
for folder in ('multiplicative_net_congestion_contract_v1_2026-10-10','multiplicative_occupancy_contract_v1_2026-10-10','multiplicative_model_source_lineage_v1_2026-10-10'):
 p=R/'experiments'/folder/'verification.json';v=json.loads(p.read_text());assert all(sha(q)==h for q,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(p)]=sha(p)
(O/'startup.json').write_text(json.dumps(dict(bindings=bindings,connections=115572,rounds=2,factors='acc1/pres1',scope='New trajectory, all physical/event/objective audits required; native quality and end-to-end gain unproven'),indent=2)+'\n')
tick=time.perf_counter()
with (O/'model.log').open('w') as f:
 code=subprocess.call([sys.executable,str(R/'tools/run_criticality_multiplicative_guard_model_v1.py'),str(R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/demand/mmc/endpoints.json'),str(O/'model')],cwd=R,stdout=f,stderr=subprocess.STDOUT)
(O/'model_terminal.json').write_text(json.dumps(dict(exit_status=code,model_process_seconds=time.perf_counter()-tick,independent_new_trajectory_audits_complete=False),indent=2)+'\n')
print('MULTIPLICATIVE MODEL TERMINAL',code,flush=True);raise SystemExit(code)
