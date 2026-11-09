"""All3 x both initializers x all-NET/live eligibility. Full audits before labels."""
import json,sys,subprocess,resource,concurrent.futures,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from source_binding_v2 import closure
from pre_route_endpoints import sha
E=R/'experiments';D=E/'prospective_external_family_live_eligibility_trial_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def limit():resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
def main():
 proofs=[E/'live_eligibility_real_pipeline_contract_v1_2026-10-20/verification.json',E/'live_overuse_eligibility_contract_v1_2026-10-20/verification.json',E/'live_overuse_eligibility_design_v1_2026-10-20/protocol.json'];bindings={}
 for p in proofs:
  v=read(p);assert all(sha(k)==h for k,h in v['bindings'].items());bindings[str(p)]=sha(p)
 prior=E/'prospective_external_family_fixed_nominal_ablation_v1_2026-10-19/protocol.json';cases=read(prior)['cases'];assert len(cases)==3;bindings[str(prior)]=sha(prior);scripts=[Path(__file__),R/'tools/run_live_eligibility_case_v1.py',R/'tools/run_external_live_eligibility_feedback_v1.py',R/'tools/verify_external_live_eligibility_feedback_events_v1.py',R/'tools/evaluate_live_eligibility_trial_v1.py',R/'tools/verify_live_eligibility_trial_metrics_v1.py',R/'tools/summarize_live_eligibility_trial_v1.py'];bindings.update(closure(scripts));epoch=E/'prospective_external_family_corrected_native_epoch_v1_2026-10-19/epoch_audit.json';unavailable=read(epoch)['unavailable_cases'];assert len(unavailable)==6;bindings[str(epoch)]=sha(epoch);D.mkdir(exist_ok=False)
 (D/'protocol.json').write_text(json.dumps(dict(cases=cases,source_history_prior=None,bindings=bindings,arms=12,max_parallel_cases=3,per_case_AS_limit_GiB=32,unavailable_cases=unavailable,all9_availability_pass=False,policy='All3 x raw_min/native_retained x all-NET control/live current-owner eligibility. Both source prior OFF. Same warm initial paths/epochs/floors/native-anchored budgets, static spans/history round rule, fixed nominal round-updated timing,10000-label repair and all guards. Exactly2rounds sorted full NET decisions. Before each live NET use actual current old support and uniqueNET occupancy/capacity, endpoint-dirty or overused required. Skip has explicit decision, no search ticket, no path/ledger/price/epoch change. Source design frozen before implementation; no static round-start mask, forced timing/hold native equivalence or native utility claim. Off states reproduce archives, full skip/current predicate and original physical/price/timing audits before unchanged quality metrics. No target-native/label-guided eligibility or dropped cases; include all checking/setup costs, not full paid pipeline acceptance'),indent=2)+'\n')
 def run(c):
  out=D/c['case'];out.mkdir(parents=True);start=time.perf_counter()
  with (out/'case.log').open('x') as log:code=subprocess.run([sys.executable,str(R/'tools/run_live_eligibility_case_v1.py'),c['case']],cwd=R,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limit).returncode
  row=dict(case=c['case'],exit_status=code,seconds=time.perf_counter()-start);(out/'terminal.json').write_text(json.dumps(row,indent=2)+'\n');print(json.dumps(row),flush=True);return row
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,cases))
 assert all(sha(k)==h for k,h in bindings.items());(D/'terminal.json').write_text(json.dumps(dict(rows=rows,bindings=bindings),indent=2)+'\n')
 if any(q['exit_status'] for q in rows):raise RuntimeError('case failure; evaluation not started')
 for script,logname in [('evaluate_live_eligibility_trial_v1.py','evaluation.log'),('verify_live_eligibility_trial_metrics_v1.py','independent_metrics.log')]:
  with (D/logname).open('x') as log:subprocess.run([sys.executable,str(R/'tools'/script)],cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True)
 (D/'evaluation_terminal.json').write_text(json.dumps(dict(exit_status=0,all12_arm_audits_and_independent_metrics_complete=True),indent=2)+'\n')
if __name__=='__main__':main()
