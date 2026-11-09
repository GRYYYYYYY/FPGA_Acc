"""All3 development cases, symmetric retry off/on, unmodified acceptance gates."""
import json,sys,subprocess,resource,concurrent.futures,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
E=R/'experiments';D=E/'prospective_external_family_capacity_retry_v1_2026-10-20';A=E/'prospective_external_family_fixed_nominal_ablation_v1_2026-10-19'
def limit():resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
def main():
 proofs=[E/'capacity_admissible_tree_contract_v2_2026-10-20/verification.json',E/'capacity_admissible_NET_candidate_contract_v2_2026-10-20/verification.json',E/'capacity_retry_event_auditor_contract_v1_2026-10-20/verification.json',A/'research_decision_v1.json'];bindings={}
 for p in proofs:
  v=json.loads(p.read_text());assert all(sha(k)==h for k,h in v['bindings'].items());bindings[str(p)]=sha(p)
 scripts=[Path(__file__),R/'tools/run_capacity_retry_case_v1.py',R/'tools/run_external_capacity_retry_v1.py',R/'tools/verify_external_capacity_retry_events_v1.py'];bindings.update(closure(scripts));cases=json.loads((A/'protocol.json').read_text())['cases'];assert len(cases)==3;D.mkdir(exist_ok=False)
 (D/'protocol.json').write_text(json.dumps(dict(cases=cases,bindings=bindings,policy='ALL3 native-retained round-updated,2rounds,10000label limit,all NET numeric order. OFF must exactly match archived states/events/timing before ON. Retry only on original positive overflow delta at same owner-excluded snapshot; complete raw-budget paths and common objective+overflow guard still required. All cases retained. Zero admissible bound avoids pertarget fullgraph reverse-vector accumulation; UNKNOWN keeps original rejection. No labels in producer, no acceptance threshold changes.',max_parallel_cases=3,per_case_address_limit_GiB=32),indent=2)+'\n')
 def run(c):
  out=D/c['case'];out.mkdir(parents=True);start=time.perf_counter()
  with (out/'case.log').open('x') as log:code=subprocess.run([sys.executable,str(R/'tools/run_capacity_retry_case_v1.py'),c['case']],cwd=R,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limit).returncode
  row=dict(case=c['case'],exit_status=code,seconds=time.perf_counter()-start,log=str(out/'case.log'));(out/'terminal.json').write_text(json.dumps(row,indent=2)+'\n');print(json.dumps(row),flush=True);return row
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,cases))
 assert all(sha(k)==h for k,h in bindings.items());(D/'terminal.json').write_text(json.dumps(dict(status='ALL3_CAPACITY_RETRY_CASE_WRAPPERS_TERMINAL',rows=rows,bindings=bindings),indent=2)+'\n')
if __name__=='__main__':main()
