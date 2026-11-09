"""Single-owner cost qualification -> full paired trial -> independent metrics.
Never restarts a missing experiment; every stage has terminal evidence.
"""
import os,sys,json,time,subprocess,hashlib,datetime
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'bound_group_refinement_launch_chain_v1_2026-10-20';T=E/'prospective_external_family_bound_group_refinement_v1_2026-10-20';C=E/'compact_bounds_all_targets_cost_v1_2026-10-20'
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from source_binding_v2 import closure
def ticks(pid):
 try:return Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[19]
 except FileNotFoundError:return None
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 pid=int(sys.argv[1]);identity=sys.argv[2];assert ticks(pid)==identity;assert not T.exists();D.mkdir(exist_ok=False)
 scripts=[Path(__file__),R/'tools/verify_compact_bounds_all_targets_cost_v1.py',R/'tools/run_bound_group_refinement_trial_v1.py',R/'tools/run_bound_group_refinement_case_v1.py',R/'tools/verify_sequential_group_refinement_v1.py',R/'tools/evaluate_bound_group_refinement_v1.py',R/'tools/verify_bound_group_refinement_metrics_v1.py'];bindings=closure(scripts)
 (D/'protocol.json').write_text(json.dumps(dict(source_pid=pid,source_startticks=identity,bindings=bindings,stages=['wait_same_cost_pid','independent_cost_accounting','all3_full_zero_vs_compact_bound_pairs','original_forecast_metrics','independent_metric_vectors_and_gates'],policy='No restarts or case selection. All inputs, budgets, labels ceiling and quality gates unchanged. Cache retained payload <=2GiB. Component costs only, no whole-pipeline speed or native QoR claim.'),indent=2)+'\n')
 def save(status,**extra):
  p=D/'state.json';tmp=p.with_suffix('.json.tmp');tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**extra),indent=2)+'\n');os.replace(tmp,p);print(status,flush=True)
 def run(script,log):
  assert all(sha(p)==h for p,h in bindings.items())
  with (D/log).open('x') as out:code=subprocess.run([sys.executable,str(R/'tools'/script)],cwd=R,stdout=out,stderr=subprocess.STDOUT).returncode
  if code:save('STOPPED_STAGE_FAILURE',script=script,exit_status=code);sys.exit(code)
 save('WAITING_SAME_COST_PROCESS',cost_pid=pid)
 while ticks(pid)==identity:time.sleep(10)
 if not (C/'verification.json').exists():save('STOPPED_COST_PROCESS_GONE_WITHOUT_COMPLETION');sys.exit(1)
 save('VERIFYING_FULL_TARGET_COST');run('verify_compact_bounds_all_targets_cost_v1.py','cost_accounting.log');cost=json.loads((C/'verification.json').read_text());assert cost['final_stats']['cached_payload_bytes']<=2*2**30 and cost['cold_seconds']>0;assert not T.exists()
 save('RUNNING_ALL3_FULL_ZERO_VS_BOUND',cost_verification=str(C/'independent_accounting_verification.json'));run('run_bound_group_refinement_trial_v1.py','full_trial.log');terminal=json.loads((T/'terminal.json').read_text());assert len(terminal['rows'])==3
 if any(q['exit_status'] for q in terminal['rows']):save('STOPPED_CASE_FAILURE_NO_EVALUATION',rows=terminal['rows']);sys.exit(1)
 save('EVALUATING_ALL6_ADMITTED_ARMS');run('evaluate_bound_group_refinement_v1.py','evaluation.log');save('INDEPENDENT_METRICS_VERIFYING');run('verify_bound_group_refinement_metrics_v1.py','independent_metrics.log');save('ALL_TRIAL_AND_EVALUATION_STAGES_TERMINAL',exit_status=0,scope='Terminal experiment, not achieved overall RouteCast objective.')
if __name__=='__main__':main()
