"""Bounded three-case queue; each case executes all four frozen-design arms."""
import json,sys,subprocess,concurrent.futures,resource,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from source_binding_v2 import closure
from pre_route_endpoints import sha
E=R/'experiments';D=E/'prospective_external_family_fixed_nominal_ablation_v1_2026-10-19'
def limit():
 resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
def main():
 preflight=E/'prospective_external_family_fixed_nominal_independent_preflight_v1_2026-10-19/verification.json';assert json.loads(preflight.read_text())['status']=='ALL6_INDEPENDENT_XML_ROUND_TIMING_AUDIT_PASS'
 prior=E/'prospective_external_family_corrected_epoch_predictions_v1_2026-10-19/protocol.json';old=json.loads(prior.read_text());assert all(sha(k)==h for k,h in old['bindings'].items());design=E/'prospective_external_family_fixed_nominal_feedback_contract_v2_2026-10-19/ablation_design_v1.json';scripts=[Path(__file__),R/'tools/run_fixed_nominal_ablation_case_v1.py',R/'tools/run_external_fixed_nominal_feedback_v1.py',R/'tools/verify_external_fixed_nominal_feedback_events_v1.py'];bindings=closure(scripts);bindings.update({str(p):sha(p) for p in [prior,design,preflight]});D.mkdir(exist_ok=False);cases=old['cases'];assert len(cases)==3
 (D/'protocol.json').write_text(json.dumps(dict(cases=cases,bindings=bindings,design=json.loads(design.read_text()),arms=12,max_parallel_case_processes=3,per_case_AS_limit_GiB=32,policy='All3 x both initializers x frozen/updated. No run dropped. Round0 identity required. Original metrics and all negative findings retained; timing model is fixed nominal local pin components.'),indent=2)+'\n')
 def run(c):
  out=D/c['case'];out.mkdir(parents=True);start=time.perf_counter();cmd=[sys.executable,str(R/'tools/run_fixed_nominal_ablation_case_v1.py'),c['case']]
  with (out/'case.log').open('x') as log:code=subprocess.run(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limit).returncode
  row=dict(case=c['case'],exit_status=code,seconds=time.perf_counter()-start,log=str(out/'case.log'));(out/'terminal.json').write_text(json.dumps(row,indent=2)+'\n');print(json.dumps(row),flush=True);return row
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,cases))
 assert all(sha(k)==h for k,h in bindings.items());(D/'terminal.json').write_text(json.dumps(dict(status='ALL3_CASE_WRAPPERS_TERMINAL',rows=rows,bindings=bindings),indent=2)+'\n')
if __name__=='__main__':main()
