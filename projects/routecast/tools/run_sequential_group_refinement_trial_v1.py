"""All fixed all-RR pair schedules, paired off/on across all3 development cases."""
import json,sys,subprocess,resource,concurrent.futures,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
E=R/'experiments';A=E/'prospective_external_family_fixed_nominal_ablation_v1_2026-10-19';D=E/'prospective_external_family_sequential_group_refinement_v1_2026-10-20'
def limit():resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
def main():
 names=['group_criticality_copy_equivalence_v1_2026-10-20','group_vacancy_proposal_contract_v3_2026-10-20','group_shared_owner_counts_contract_v3_2026-10-20','group_draft_frame_contract_v2_2026-10-20','sequential_group_refinement_contract_v1_2026-10-20','group_refinement_real_trace_contract_v1_2026-10-20'];proofs=[E/name/'verification.json' for name in names]+[E/'prospective_external_family_blocker_root_pair_schedule_v2_2026-10-20/independent_verification_v1.json',A/'research_decision_v1.json'];bindings={}
 for p in proofs:
  v=json.loads(p.read_text());assert all(sha(k)==h for k,h in v['bindings'].items());bindings[str(p)]=sha(p)
 scripts=[Path(__file__),R/'tools/run_group_refinement_case_v1.py',R/'tools/verify_sequential_group_refinement_v1.py'];bindings.update(closure(scripts));cases=json.loads((A/'protocol.json').read_text())['cases'];assert len(cases)==3;D.mkdir(exist_ok=False);policy='All3 paired off/on, all8290/8326/8337 all-RR blocking-owner pairs from fixed baseline in stable numeric order. Each ON pair has fresh current ledger/member epochs, detached old records,10000 labels per query and zero admissible bound. Fixed baseline final history/round1 criticality for the whole refinement, no STA refresh. Explicit batch common-owner-release objective, unchanged raw budgets and fullgraph overflow nonincrease. Identical complete proposals are no-ops. UNKNOWN/rejection no state change. Every256 groups plus terminal actual state digest; independent all-event/XML replay before metrics. No labels in producer or search/quality-based schedule filtering. IPIN remapping nominal-timing limitation remains; this is not native legality/QoR/end-to-end speed acceptance.'
 (D/'protocol.json').write_text(json.dumps(dict(cases=cases,bindings=bindings,policy=policy,max_parallel_cases=3,per_case_address_limit_GiB=32,component_timing_only=True,all9_availability_pass=False),indent=2)+'\n')
 def run(c):
  out=D/c['case'];out.mkdir(parents=True);start=time.perf_counter()
  with (out/'case.log').open('x') as log:code=subprocess.run([sys.executable,str(R/'tools/run_group_refinement_case_v1.py'),c['case']],cwd=R,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limit).returncode
  row=dict(case=c['case'],exit_status=code,seconds=time.perf_counter()-start,log=str(out/'case.log'));(out/'terminal.json').write_text(json.dumps(row,indent=2)+'\n');print(json.dumps(row),flush=True);return row
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,cases))
 assert all(sha(k)==h for k,h in bindings.items());(D/'terminal.json').write_text(json.dumps(dict(status='ALL3_FULL_SEQUENTIAL_GROUP_REFINEMENT_CASE_WRAPPERS_TERMINAL',rows=rows,bindings=bindings),indent=2)+'\n')
if __name__=='__main__':main()
