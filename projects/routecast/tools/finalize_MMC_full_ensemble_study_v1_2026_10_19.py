"""Wait exact check chain, independently audit metrics, preserve bounded decision."""
import pathlib,json,hashlib,subprocess,sys,time
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def identity(pid):
 try:s=pathlib.Path(f'/proc/{pid}/stat').read_text()
 except FileNotFoundError:return None
 return int(s[s.rfind(')')+2:].split()[19])
def write(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
def main():
 pid,ticks=map(int,sys.argv[1:]);assert identity(pid)==ticks;C=R/'experiments/mmc_full_ensemble_checks_v1_2026-10-19';O=R/'experiments/mmc_full_ensemble_final_review_v1_2026-10-19';O.mkdir();script=R/'tools/verify_MMC_full_NET_ensemble_metrics_v1_2026_10_19.py';contract=R/'experiments/mmc_full_NET_ensemble_fraction_metric_contract_v1_2026-10-19/verification.json';files=[pathlib.Path(__file__).resolve(),script,contract,C/'protocol.json'];bindings={str(p):sha(p) for p in files};write(O/'protocol.json',dict(bindings=bindings,upstream_pid=pid,upstream_start_ticks=ticks,poll_seconds=30,restart_any_job=False,scope='Independent final metric audit and factual study decision only; no model promotion, experiment tuning or overall goal completion.'));print('WAITING EXACT AUDIT/EVAL CHAIN',pid,ticks,flush=True)
 while identity(pid)==ticks:time.sleep(30)
 terminal=C/'terminal.json'
 if not terminal.exists() or json.loads(terminal.read_text())['status']!='FULL_PREDICTION_AUDIT_AND_DEVELOPMENT_EVALUATION_COMPLETE':
  write(O/'terminal.json',dict(status='UPSTREAM_FAILED_OR_UNPROVEN'));raise SystemExit(1)
 for p,h in bindings.items():assert sha(p)==h,p
 with (O/'metric_audit.log').open('x') as f:code=subprocess.run([sys.executable,str(script)],cwd=R,stdout=f,stderr=subprocess.STDOUT).returncode
 if code:write(O/'terminal.json',dict(status='INDEPENDENT_METRIC_AUDIT_FAILED',exit_code=code));raise SystemExit(code)
 Q=R/'experiments/mmc_full_NET_tree_ensemble_quality_v1_2026-10-19';rp=Q/'results.json';vp=Q/'independent_metric_verification_v1.json';result=json.loads(rp.read_text());v=json.loads(vp.read_text());assert v['status']=='all3_full_NET_ensemble_metrics_and_development_decisions_independently_verified' and v['bindings'][str(rp)]==sha(rp)
 decision=dict(status='DEVELOPMENT_COHORT_PRIMARY_GATE_PASSED' if result['all3_primary_gate_pass'] else 'DEVELOPMENT_COHORT_PRIMARY_GATE_NOT_PASSED',bindings={**bindings,str(terminal):sha(terminal),str(rp):sha(rp),str(vp):sha(vp)},case_gates=[dict(case=row['case'],primary_gate=row['primary_gate']) for row in result['cases']],all3_primary_gate_pass=result['all3_primary_gate_pass'],candidate_promoted=False,strict_unseen_family_admitted=False,native_utility_proven=False,complete_workflow_gain_proven=False,all_NET_global_shortest_duals_proven=False,hardware_gain_proven=False,scope='Complete3known-MMC development-layout forecast study under fixed rules. Any positive result remains development evidence only. No after-outcome changes to cases, models, controls, K or metrics; no global goal completion claim.')
 write(Q/'research_decision_v1.json',decision);write(O/'terminal.json',dict(status='STUDY_METRICS_INDEPENDENTLY_VERIFIED_DECISION_SAVED',decision=str(Q/'research_decision_v1.json'),full_research_goal_complete=False));print(decision['status'],flush=True)
if __name__=='__main__':main()
