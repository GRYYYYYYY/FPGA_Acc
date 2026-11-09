"""Fresh cold generation included in subsequent repair workflow clock."""
import json,subprocess,time,sys,runpy,contextlib
import shared_repair_runtime_v1 as runtime
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
D=R/'experiments/adder_shared_full_cost_v1_2026-10-08';D.mkdir(exist_ok=False)
stages=['shared_full_step_0_v1.py', 'shared_full_step_1_v1.py', 'shared_full_step_2_v1.py', 'shared_full_step_3_v1.py', 'shared_full_step_4_v1.py', 'shared_full_step_5_v1.py', 'shared_full_step_6_v1.py', 'shared_full_step_7_v1.py', 'shared_full_step_8_v1.py', 'shared_full_step_9_v1.py', 'shared_full_step_10_v1.py', 'shared_full_step_11_v1.py', 'shared_full_step_12_v1.py', 'shared_full_step_13_v1.py', 'shared_full_step_14_v1.py', 'shared_full_step_15_v1.py', 'shared_full_step_16_v1.py', 'shared_full_step_17_v1.py', 'shared_full_step_18_v1.py', 'shared_full_step_19_v1.py', 'shared_full_step_20_v1.py', 'shared_full_step_21_v1.py', 'shared_full_step_22_v1.py', 'shared_full_step_23_v1.py', 'shared_full_step_24_v1.py', 'shared_full_step_25_v1.py', 'shared_full_step_26_v1.py', 'shared_full_step_27_v1.py', 'shared_full_step_28_v1.py']
inprocess=['shared_full_step_2_v1.py', 'shared_full_step_4_v1.py', 'shared_full_step_7_v1.py', 'shared_full_step_10_v1.py', 'shared_full_step_13_v1.py', 'shared_full_step_17_v1.py', 'shared_full_step_20_v1.py', 'shared_full_step_23_v1.py']
bindings=closure([Path(__file__),R/'tools/shared_repair_runtime_v1.py',*[R/'tools'/n for n in stages]])
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,stages=stages,scope='Fresh four-step cold routes + full budget/canonical checks form timed initial prefix. Repair pipeline then consumes those routes; cold production not free. All subsequent search/independent proofs/serialization/native/canonical timed. Provided graphs/netlists/placements/budgets excluded; protocol/finalreceipt/topverification excluded.'),indent=2)+'\n');start=time.perf_counter();rows=[];cold=None
for i,name in enumerate(stages):
 tick=time.perf_counter()
 with (D/(name+'.log')).open('x') as log:
  if name in inprocess:
   with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):runpy.run_path(str(R/'tools'/name),run_name='__main__')
   code=0
  else:code=subprocess.run([sys.executable,str(R/'tools'/name)],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
 rows.append(dict(script=name,seconds=time.perf_counter()-tick,exit_code=code));print(rows[-1],flush=True);assert code==0
 if i==1:cold=time.perf_counter()-start
 (D/'progress.json').write_text(json.dumps(rows,indent=2)+'\n')
runtime.shutdown();elapsed=time.perf_counter()-start;assert all(sha(f)==h for f,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,stages=rows,direct_cold_prefix_seconds=cold,coldfirst_repaired_workflow_seconds=elapsed,observed_ratio=elapsed/cold,protocol_sha256=sha(D/'protocol.json'),scope='One actual nested-prefix workflow measurement, not independent paired arms. Includes all cold production and repair checks; no complete original-input or runtime gain claim.'),indent=2)+'\n');print(cold,elapsed,elapsed/cold)
