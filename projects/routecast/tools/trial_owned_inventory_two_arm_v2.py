"""Fresh complete two arms including external archive parity verification costs."""
import json,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/owned_inventory_two_arm_v2_2026-10-08';D.mkdir(exist_ok=False)
files=[Path(__file__),R/'tools/run_owned_inventory_native_audit_arm_v2.py',R/'tools/verify_owned_inventory_native_audit_arm_v2.py']
bindings={str(p):sha(p) for p in files}
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,order=['seed','cold'],scope='Fresh provided-input two arms, each full native/shared inventory audit and external complete archive parity checks included in subprocess stage clocks. Initial wrapper protocol/final wrapper receipt excluded; no original input generation or canonical pin/HDL equivalence.'),indent=2)+'\n')
results={}
for arm in ('seed','cold'):
 start=time.perf_counter();stages=[]
 for script in ('run_owned_inventory_native_audit_arm_v2.py','verify_owned_inventory_native_audit_arm_v2.py'):
  tick=time.perf_counter()
  with (D/f'{arm}_{script}.log').open('x') as log:code=subprocess.run(['python3',str(R/'tools'/script),arm,str(D/arm)],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
  stages.append(dict(script=script,exit_code=code,seconds=time.perf_counter()-tick));print(arm,stages[-1],flush=True)
  assert code==0
 results[arm]=dict(stages=stages,declared_seconds=time.perf_counter()-start)
 (D/'progress.json').write_text(json.dumps(results,indent=2)+'\n')
assert all(sha(f)==h for f,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,arms=results,protocol_sha256=sha(D/'protocol.json')),indent=2)+'\n');print(results)
