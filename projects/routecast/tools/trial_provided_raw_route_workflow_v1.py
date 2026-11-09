"""One prospective wall clock from provided post-resume route to native quality."""
import json
import subprocess
import time
from pathlib import Path
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]
D=R/'experiments/provided_raw_route_workflow_v1_2026-10-08'
D.mkdir(exist_ok=False)
names=('trial_raw_route_candidate_pipeline_v4.py','verify_raw_route_candidate_pipeline_v4.py',
       'trial_raw_candidate_native_reload_v2.py','verify_raw_candidate_reconciled_dump_v2.py',
       'trial_raw_candidate_canonical_v2.py','verify_raw_candidate_canonical_v2.py',
       'verify_raw_candidate_native_quality_v2.py')
case=next(c for c in json.loads((R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json').read_text())['cases'] if c['width']==32 and c['index']==2)
inputs=[Path(case['target']),Path(case['budget']),R/'experiments/native_resume_branch_partial_v8_2026-10-08/resume/output.route',
        R/'experiments/mux_old_full_timing_graph_2026-10-06/w32_timing_graph.json',
        R/'experiments/mux_full_timing_rr_2026-10-06/w32.json',
        R/'experiments/mux_allfanin_budgets_2026-10-06/w32_m2.json']
bindings={str(path):sha(path) for path in inputs}
for name in names:bindings[str(R/'tools'/name)]=sha(R/'tools'/name)
bindings[str(Path(__file__))]=sha(Path(__file__))
scope='Single observed workflow from PROVIDED raw post-resume route plus endpoints/original budgets/model/packed identity inputs. Includes all subprocess startup/shutdown, candidate final JSON output, exact trace verification, serialization, native FULL STA, post-sync/canonical audits, quality comparison. Excludes generating provided input artifacts, initial protocol setup and final wrapper receipt/fee audit. Historical trace checks are development validation, not a general unseen-input proof. No full original-input or paired speedup claim; two original budget failures retained.'
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,stages=names,scope=scope),indent=2)+'\n')
started=time.perf_counter();stages=[]
for name in names:
 tick=time.perf_counter()
 with (D/(name+'.log')).open('w') as log:
  code=subprocess.run(['python3',str(R/'tools'/name)],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
 stages.append(dict(script=name,exit_code=code,elapsed_seconds=time.perf_counter()-tick))
 (D/'progress.json').write_text(json.dumps(stages,indent=2)+'\n')
 print(stages[-1],flush=True)
 if code:raise RuntimeError('stage failed: '+name)
elapsed=time.perf_counter()-started
assert all(sha(path)==digest for path,digest in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,protocol_sha256=sha(D/'protocol.json'),stages=stages,
 provided_route_workflow_seconds=elapsed,full_original_input_workflow_seconds=None,scope=scope),indent=2)+'\n')
print('provided-route workflow terminal',elapsed,flush=True)
