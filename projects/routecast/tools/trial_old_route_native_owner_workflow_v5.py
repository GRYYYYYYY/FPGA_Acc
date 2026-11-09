"""One prospective wall clock from provided post-resume route to native quality."""
import json
import subprocess,runpy,contextlib,gc
from class_cached_rc_endpoint_session_v2 import clear_cache,STATS
import time
from pathlib import Path
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]
D=R/'experiments/old_route_native_owner_workflow_v5_2026-10-08'
D.mkdir(exist_ok=False)
names=('trial_fresh_retained_branch_seed_v9.py', 'verify_fresh_retained_branch_seed_v9.py', 'native_resume_prototype/trial_fresh_retained_branch_resume_v9.py', 'verify_fresh_retained_branch_resume_v9.py', 'verify_fresh_retained_branch_resume_parity_v10.py', 'trial_raw_route_native_owner_candidate_v5.py', 'verify_raw_route_native_owner_candidate_v5.py', 'trial_native_owner_candidate_reload_v5.py', 'verify_native_owner_candidate_dump_v5.py', 'trial_native_owner_candidate_canonical_v5.py', 'verify_native_owner_candidate_canonical_v5.py', 'verify_native_owner_candidate_quality_v5.py', 'verify_native_owner_candidate_entry_v5.py')
case=next(c for c in json.loads((R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json').read_text())['cases'] if c['width']==32 and c['index']==2)
inputs=[Path(case['target']),Path(case['budget']),R/'work/mux_crossbar_channel_pressure_2026-10-06/mux_w32_c128/design.route',Path(case['old']),
        R/'experiments/mux_old_full_timing_graph_2026-10-06/w32_timing_graph.json',
        R/'experiments/mux_full_timing_rr_2026-10-06/w32.json',
        R/'experiments/mux_allfanin_budgets_2026-10-06/w32_m2.json']
inputs.extend([R/'work/mux_crossbar_channel_pressure_2026-10-06/mux_w32_c128/design.blif',R/'work/mux_crossbar_channel_pressure_2026-10-06/mux_w32_c128/design.net',R/'experiments/mux_budget_move_cohort_2026-10-06/w32_m2/target.place'])
bindings={str(path):sha(path) for path in inputs}
for name in names:bindings[str(R/'tools'/name)]=sha(R/'tools'/name)
bindings[str(Path(__file__))]=sha(Path(__file__))
scope='Single observed workflow from PROVIDED old accepted route plus endpoints/original budgets/model/original packed netlist and target placement inputs. Includes a cold in-process authenticated RR template build in fresh seed and one cache hit with independent CSR/RC clone in candidate, full cache authentication/clone and same-process execution/garbage collection, fresh retained forest/seed generation, actual partial native resume, all subprocess startup/shutdown, reused exact native minRC/clipped certificate context with incremental isolated owner ledger and single direct dynamic scan without preliminary wire scans, candidate final JSON output, exact trace verification, fresh original-input identity capture, serialization, native FULL STA, post-sync/canonical audits, quality comparison. Excludes generating provided input artifacts, initial protocol setup and final wrapper receipt/fee audit. Historical trace checks are development validation, not a general unseen-input proof. No full original-input or paired speedup claim; two original budget failures retained.'
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,stages=names,scope=scope),indent=2)+'\n')
clear_cache()
started=time.perf_counter();stages=[]
for name in names:
 tick=time.perf_counter()
 with (D/(Path(name).name+'.log')).open('w') as log:
  if name in ('trial_fresh_retained_branch_seed_v9.py','trial_raw_route_native_owner_candidate_v5.py'):
   with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
    runpy.run_path(str(R/'tools'/name),run_name='__main__')
    gc.collect()
   code=0
  else:
   code=subprocess.run(['python3',str(R/'tools'/name)],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
 stages.append(dict(script=name,exit_code=code,elapsed_seconds=time.perf_counter()-tick,session_cache_stats=dict(STATS)))
 (D/'progress.json').write_text(json.dumps(stages,indent=2)+'\n')
 print(stages[-1],flush=True)
 if code:raise RuntimeError('stage failed: '+name)
elapsed=time.perf_counter()-started
assert all(sha(path)==digest for path,digest in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,protocol_sha256=sha(D/'protocol.json'),stages=stages,
 session_cache_stats=dict(STATS),declared_input_workflow_seconds=elapsed,full_original_input_workflow_seconds=None,scope=scope),indent=2)+'\n')
print('provided-route workflow terminal',elapsed,flush=True)
