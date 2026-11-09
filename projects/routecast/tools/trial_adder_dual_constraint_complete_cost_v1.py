"""Fresh two-arm declared-input workflow costs with complete validation stages."""
import json,subprocess,time,sys
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
D=R/'experiments/adder_dual_constraint_complete_cost_v1_2026-10-08';D.mkdir(exist_ok=False)
arms=dict(seed=['trial_adder_capacity_budget_wire_guard_v2.py','verify_adder_capacity_budget_wire_guard_v2.py','trial_adder_capacity_budget_multinet_wire_guard_v2.py','verify_adder_capacity_budget_multinet_wire_guard_v2.py','verify_adder_multinet_wire_bounds_v2.py','serialize_adder_multinet_wire_guard_v2.py','trial_adder_wire_guard_native_reload_v2.py','trial_adder_wire_guard_canonical_reload_v2.py'],cold=['trial_adder_wire_guard_matched_cold_v2.py','trial_adder_wire_guard_matched_cold_canonical_v2.py'])
bindings=closure([Path(__file__),*[R/'tools'/n for names in arms.values() for n in names]])
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,arms=arms,scope='All4 provided oldnative routes/target endpoints/existing model budgets; seed coldprepare+branch/group search+all independent validation/serialization/native/canonical, cold actualnative/fullbudget/canonical. Supplied inputs and original baseline native production excluded; initial protocol/finaltopreceipt/topqualityverifier excluded.'),indent=2)+'\n');results={}
for arm,names in arms.items():
 start=time.perf_counter();stages=[]
 for name in names:
  tick=time.perf_counter()
  with (D/f'{arm}_{name}.log').open('x') as log:code=subprocess.run([sys.executable,str(R/'tools'/name)],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
  stages.append(dict(script=name,exit_code=code,seconds=time.perf_counter()-tick));print(arm,stages[-1],flush=True);assert code==0
 results[arm]=dict(stages=stages,seconds=time.perf_counter()-start)
 (D/'progress.json').write_text(json.dumps(results,indent=2)+'\n')
assert all(sha(f)==h for f,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,arms=results,protocol_sha256=sha(D/'protocol.json')),indent=2)+'\n');print(results)
