"""Independent all3 old branch-pruned current-pin/capacity/partition proofs."""
import json,sys,subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
D=R/'experiments/mmc_old_branch_prune_seeds_v1_2026-10-18';gp=D/'generation_complete.json';g=json.loads(gp.read_text());assert g['all3_branch_pruned_seeds_generated'];bindings={**g['bindings'],**closure([Path(__file__),R/'tools/verify_mmc_old_branch_prune_seed_v1_2026_10_18.py']),str(gp):sha(gp)};rows=[]
def run(case):
 with (D/(case+'_audit.log')).open('x') as log:code=subprocess.call([sys.executable,str(R/'tools/verify_mmc_old_branch_prune_seed_v1_2026_10_18.py'),str(R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18'/case),str(D/case)],cwd=R,stdout=log,stderr=subprocess.STDOUT)
 print('BRANCH SEED AUDIT',case,code,flush=True);return dict(case=case,exit_code=code)
with ThreadPoolExecutor(max_workers=3) as pool:
 for future in as_completed([pool.submit(run,c) for c in ['case_01','case_02','case_03']]):rows.append(future.result());(D/'audit_stages.json').write_text(json.dumps(rows,indent=2))
assert all(x['exit_code']==0 for x in rows)
for row in rows:
 proof=D/row['case']/'independent_verification_v1.json';v=json.loads(proof.read_text());assert v['complete_disjoint_selected_pending_partition'] and v['all_selected_terminal_paths_and_printed_node_records_reused_from_old_native'] and v['all_current_native_local_pins_and_endpoints_match'] and v['uniqueNET_occupancy_monotone_subset_of_authenticated_old_legal_state'];bindings.update(v['bindings']);bindings[str(proof)]=sha(proof)
assert all(sha(p)==h for p,h in bindings.items())
with (D/'seed_admission_verification_v1.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,rows=rows,all3_partialNET_old_branch_seeds_independently_admitted=True,scope='Selected unchanged paths/current pins and monotone old-graph capacity reuse only. Native partial tree support and complete route pending.'),f,indent=2)
