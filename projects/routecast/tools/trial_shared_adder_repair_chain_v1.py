"""Real eight-stage in-process repair chain, original outputs fully compared."""
import json,runpy,time,sys
from pathlib import Path
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
import shared_repair_runtime_v1 as runtime
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'shared_adder_repair_chain_v1_2026-10-09';D.mkdir(exist_ok=False)
bases=['adder_matched_baseline_branch_repair_v3','adder_matched_baseline_multinet_repair_v3','adder_matched_baseline_reverse_group_repair_v2','adder_twohop_group_repair_v2','adder_failed_constraint_probe_v2','adder_tight_budget_order_repair_v2','adder_failure_priority_retry_v2','adder_live_owner_expansion_v2']
stages=[R/f'tools/trial_adder_shared_chain_stage_{i}_v1.py' for i in range(8)];bindings=closure([Path(__file__),*stages]);rows=[];start=time.perf_counter()
try:
 for i,path in enumerate(stages):
  tick=time.perf_counter();runpy.run_path(str(path),run_name='__main__');rows.append(dict(stage=i,seconds=time.perf_counter()-tick));print(rows[-1],flush=True)
 elapsed=time.perf_counter()-start;assert runtime.leases==8
finally:runtime.shutdown()
for i,base in enumerate(bases):
 for step in range(4):
  a=E/f'{base}_2026-10-08/step_{step}.json';b=E/f'adder_shared_chain_stage_{i}_v1_2026-10-08/step_{step}.json';assert json.loads(a.read_text())==json.loads(b.read_text()),(i,step)
  for p in (a,b):bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items())
out=dict(bindings=bindings,rows=rows,whole_repair_chain_seconds=elapsed,all32_full_stage_outputs_equal=True,native_handles_created=1,scope='Eight real stages use one immutable context and one nativehandle; fresh endpoint input hashes each stage/step. Includes state serialization and internal checks, excludes external independent proof/native reload/cold production and final parity. No complete workflow gain.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(elapsed)
