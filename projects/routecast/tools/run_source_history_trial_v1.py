"""All3 x both initializers x zero/source prior. Full audits before labels."""
import json,sys,subprocess,resource,concurrent.futures,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from source_binding_v2 import closure
from pre_route_endpoints import sha
E=R/'experiments';D=E/'prospective_external_family_source_history_trial_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def limit():resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
def main():
 proofs=[E/'source_history_real_pipeline_contract_v1_2026-10-20/verification.json',E/'source_history_lifecycle_contract_v1_2026-10-20/verification.json',E/'source_native_history_prior_v1_2026-10-20/verification.json'];bindings={}
 for p in proofs:
  v=read(p);assert all(sha(k)==h for k,h in v['bindings'].items());bindings[str(p)]=sha(p)
 prior=E/'prospective_external_family_fixed_nominal_ablation_v1_2026-10-19/protocol.json';cases=read(prior)['cases'];assert len(cases)==3;bindings[str(prior)]=sha(prior);scripts=[Path(__file__),R/'tools/run_source_history_case_v1.py',R/'tools/run_external_source_history_feedback_v1.py',R/'tools/verify_external_source_history_feedback_events_v1.py',R/'tools/evaluate_source_history_trial_v1.py',R/'tools/verify_source_history_trial_metrics_v1.py'];bindings.update(closure(scripts));source=E/'source_native_history_prior_v1_2026-10-20/prior.json';bindings[str(source)]=sha(source);epoch=E/'prospective_external_family_corrected_native_epoch_v1_2026-10-19/epoch_audit.json';unavailable=read(epoch)['unavailable_cases'];assert len(unavailable)==6;bindings[str(epoch)]=sha(epoch);D.mkdir(exist_ok=False)
 (D/'protocol.json').write_text(json.dumps(dict(cases=cases,source_prior=str(source),bindings=bindings,arms=12,max_parallel_cases=3,per_case_AS_limit_GiB=32,unavailable_cases=unavailable,all9_availability_pass=False,policy='All3 x raw_min/native_retained x source history off/on. Same warm initial paths/epochs/floors/native-anchored raw budgets. Source prior exact acc_cost-1 added once; static spans separate; round0 no excess update; round1 add only current model overuse. Fixed nominal timing updated each round, same10000-label repair and all transaction guards, all NETs numeric order,2rounds. Off full round states and sketch must reproduce frozen baseline. No group refinement or reverse-bound cache. All full XML/price/timing audits before unchanged quality gates. Source native history only; no target-native state or target-guided arm selection. Native source reuse cost remains separately payable, no whole pipeline/net benefit or unseen-family claim.'),indent=2)+'\n')
 def run(c):
  out=D/c['case'];out.mkdir(parents=True);start=time.perf_counter()
  with (out/'case.log').open('x') as log:code=subprocess.run([sys.executable,str(R/'tools/run_source_history_case_v1.py'),c['case']],cwd=R,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limit).returncode
  row=dict(case=c['case'],exit_status=code,seconds=time.perf_counter()-start);(out/'terminal.json').write_text(json.dumps(row,indent=2)+'\n');print(json.dumps(row),flush=True);return row
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,cases))
 assert all(sha(k)==h for k,h in bindings.items());(D/'terminal.json').write_text(json.dumps(dict(rows=rows,bindings=bindings),indent=2)+'\n')
 if any(q['exit_status'] for q in rows):raise RuntimeError('case failure; evaluation not started')
 for script,logname in [('evaluate_source_history_trial_v1.py','evaluation.log'),('verify_source_history_trial_metrics_v1.py','independent_metrics.log')]:
  with (D/logname).open('x') as log:subprocess.run([sys.executable,str(R/'tools'/script)],cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True)
 (D/'evaluation_terminal.json').write_text(json.dumps(dict(exit_status=0,all12_arm_audits_and_independent_metrics_complete=True),indent=2)+'\n')
if __name__=='__main__':main()
