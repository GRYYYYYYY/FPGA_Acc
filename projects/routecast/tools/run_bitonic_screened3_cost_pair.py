"""Serial fresh optimized acceptance + equally optimized cold baseline + final proof."""
import json,subprocess,sys
from pathlib import Path
from pre_route_endpoints import sha
from freeze_priority_family import closure
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/bitonic_screened3_cost_pair_2026-10-07';out.mkdir();proof=ROOT/'experiments/priority_tree_context_2026-10-07/verification.json';assert json.loads(proof.read_text())['terminal_exit']==0
names=['run_bitonic_screened3_acceptance_workflow.py','run_bitonic_screened3_cold_cost_baseline.py','finalize_bitonic_screened3_cost.py'];sources=closure([Path(__file__),*[ROOT/'tools'/n for n in names],ROOT/'tools/owner_union_wire_rc_context_cached_tree.py']);p=dict(sources=sources,parent_proof_sha256=sha(proof),scope='Fresh prepared-input serial workflow and baseline with same private RR tree/class memo optimization. Separate Python processes; RR cache cleared at each run start, OS file caches not reset. Both internal clocks include their own mandatory validation. No historical timer stitching.');(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');rows=[]
for name in names:
 print('Starting',name,flush=True)
 with (out/(name+'.log')).open('w') as f:code=subprocess.run([sys.executable,str(ROOT/'tools'/name)],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT).returncode
 rows.append(dict(tool=name,exit_code=code,log_sha256=sha(out/(name+'.log'))));(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows,complete=len(rows)==3 and all(x['exit_code']==0 for x in rows)),indent=2)+'\n');print('Finished',name,code,flush=True)
 if code:raise SystemExit(code)
assert all(sha(f)==d for f,d in sources.items())
