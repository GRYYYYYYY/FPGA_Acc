"""Run frozen native utility5arms per3cases after complete seed admission."""
import json,sys,subprocess,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
S=R/'experiments/mmc_v2_native_seed_inputs_v1_2026-10-18';sp=S/'seed_admission_verification_v1.json';sv=json.loads(sp.read_text());assert sv['status']=='pass' and sv['all12_seeds_independently_admitted'];D=R/'experiments/mmc_v2_native_utility_v1_2026-10-18';D.mkdir();(D/'logs').mkdir();bindings={**sv['bindings'],**closure([Path(__file__),R/'tools/run_mmc_v2_native_utility_case_v1_2026_10_18.py']),str(sp):sha(sp)};P=json.loads((S/'protocol.json').read_text());rows=[]
assert all(sha(p)==h for p,h in bindings.items())
with (D/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,frozen_seed_protocol=str(S/'protocol.json'),max_parallel_cases=3,arm_order=P['native_arm_order'],scope='Correctness and deterministic native work/QoR pilot. Concurrent cases and unbalanced fixed order prevent timing benefit claims; cached prefix/seed costs excluded from component clocks.'),f,indent=2)
def run(case):
 print('NATIVE V2 CASE START',case,flush=True);tick=time.perf_counter()
 with (D/'logs'/(case+'.log')).open('x') as f:code=subprocess.call([sys.executable,str(R/'tools/run_mmc_v2_native_utility_case_v1_2026_10_18.py'),case],cwd=R,stdout=f,stderr=subprocess.STDOUT)
 row=dict(case=case,exit_code=code,seconds=time.perf_counter()-tick);print('NATIVE V2 CASE TERMINAL',row,flush=True);return row
with ThreadPoolExecutor(max_workers=3) as pool:
 for future in as_completed([pool.submit(run,c) for c in P['case_order']]):rows.append(future.result());(D/'stage_status.json').write_text(json.dumps(rows,indent=2))
if any(x['exit_code'] for x in rows):raise SystemExit(1)
for case in P['case_order']:
 proof=D/case/'verification.json';v=json.loads(proof.read_text());assert v['all_native_physical_and_canonical_pass'] and len(v['rows'])==5;bindings[str(proof)]=sha(proof)
assert all(sha(p)==h for p,h in bindings.items())
with (D/'cohort_complete.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,rows=rows,all15_native_FULL_physical_and_canonical_semantic_pass=True,utility_screen_pending=True),f,indent=2)
print('ALL15 V2NATIVE ARMS ADMITTED',flush=True)
