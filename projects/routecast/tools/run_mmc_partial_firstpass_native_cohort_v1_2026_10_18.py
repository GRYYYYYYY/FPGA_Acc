"""All3supplemental partialNET old-branch controls, unchanged final admission."""
import json,sys,subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
S=R/'experiments/mmc_old_branch_prune_seeds_v1_2026-10-18';sp=S/'seed_admission_verification_v1.json';sv=json.loads(sp.read_text());ep=R/'experiments/mmc_partial_firstpass_equivalence_on_v1_2026-10-18/equivalence_verification_v1.json';eq=json.loads(ep.read_text());assert sv['all3_partialNET_old_branch_seeds_independently_admitted'] and eq['no_seed_and_complete_NET_seed_old_behavior_equal'];offproof=R/'experiments/mmc_partial_firstpass_equivalence_off_v1_2026-10-18/equivalence_verification_v1.json';offeq=json.loads(offproof.read_text());assert offeq['no_seed_and_complete_NET_seed_old_behavior_equal'];D=R/'experiments/mmc_partial_firstpass_native_v1_2026-10-18';D.mkdir();(D/'logs').mkdir();bindings={**sv['bindings'],**eq['bindings'],**offeq['bindings'],str(offproof):sha(offproof),**closure([Path(__file__),R/'tools/run_mmc_partial_firstpass_native_case_v1_2026_10_18.py']),str(sp):sha(sp),str(ep):sha(ep)};assert all(sha(p)==h for p,h in bindings.items())
with (D/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,case_order=['case_01','case_02','case_03'],arms_by_case={c:['off','on'] for c in ['case_01','case_02','case_03']},policy='Frozen off then on for all3cases using identical seed paths; only explicit first-pass preservation switch changes. Both no-seed and completeNET baseline modes must pass equivalence before any native case.',admission='All6partial runs must complete original115572queries; native FULL/physical/canonical semantics mandatory. Flag-off outputs and integer counters must equal supported-engine prior partial controls.',scope='Supplemental exposed cheap-control study, not a replacement or alteration of failed15arm screen; no timing benefit, heldout, full-STA or hardware claim.'),f,indent=2)
def run(case):
 print('BRANCH NATIVE START',case,flush=True)
 with (D/'logs'/(case+'.log')).open('x') as log:code=subprocess.call([sys.executable,str(R/'tools/run_mmc_partial_firstpass_native_case_v1_2026_10_18.py'),case],cwd=R,stdout=log,stderr=subprocess.STDOUT)
 row=dict(case=case,exit_code=code);print('BRANCH NATIVE TERMINAL',row,flush=True);return row
rows=[]
with ThreadPoolExecutor(max_workers=3) as pool:
 for future in as_completed([pool.submit(run,c) for c in ['case_01','case_02','case_03']]):rows.append(future.result());(D/'stages.json').write_text(json.dumps(rows,indent=2))
assert all(r['exit_code']==0 for r in rows)
for case in ['case_01','case_02','case_03']:
 vp=D/case/'verification.json';v=json.loads(vp.read_text());assert v['all_native_physical_and_canonical_pass'];bindings.update(v['bindings']);bindings[str(vp)]=sha(vp)
 old=R/'experiments/mmc_old_branch_prune_native_v1_2026-10-18'/case;oldv=json.loads((old/'verification.json').read_text());a=next(r for r in v['rows'] if r['arm']=='off');b=next(r for r in oldv['rows'] if r['arm']=='old_branch_prune');assert sha(D/case/'off/output.route')==sha(old/'old_branch_prune/output.route') and a['wirelength']==b['wirelength'] and a['diagnostic_cpd_ns']==b['diagnostic_cpd_ns']
 for k in ['iterations','total_heap_pushes','total_rerouted_NET_operations','total_rerouted_connection_operations']:assert a['native_work'][k]==b['native_work'][k]
 for x,y in zip(a['native_work']['rows'],b['native_work']['rows']):
  for k in ['iteration','BB_updates','heap_pushes','rerouted_NET_operations','rerouted_connection_operations','overused_RR_nodes']:assert x[k]==y[k]
 bindings[str(old/'verification.json')]=sha(old/'verification.json')

assert all(sha(p)==h for p,h in bindings.items())
with (D/'cohort_complete.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,rows=rows,all6_off_on_complete_FULL_physical_canonical_pass=True,all3_flag_off_equal_supported_engine_partial_controls=True,independent_wire_work_and_utility_comparison_pending=True),f,indent=2)
print('ALL3PARTIAL NET NATIVE CONTROLS COMPLETE',flush=True)
