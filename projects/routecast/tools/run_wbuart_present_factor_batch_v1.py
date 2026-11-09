"""Freeze and execute all-nine full-control present-factor-only trial."""
import json,subprocess,sys,resource,concurrent.futures,time
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_present_factor_trial_v1_2026-10-20'
def read(p):return json.loads(p.read_text())
def main():
 D.mkdir(exist_ok=False);preflight=read(E/'wbuart_present_factor_preflight_v1_2026-10-20/verification.json');assert preflight['status']=='FIRST_CASE_FACTOR1_CONTROL_EXACT_PARITY_AND0_HALF_COMPLETE_AUDIT_PASS';assert all(sha(p)==h for p,h in preflight['bindings'].items());original=read(E/'wbuart_forecasts_v1_2026-10-20/manifest.json');workflow=read(E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json');cases=[]
 for c in original['cases']:
  c=dict(c);c['output']=str(D/c['case']);c['old_specification']=next(r['specification'] for r in workflow['comparisons'] if r['case']==c['case']);cases.append(c)
 files=[Path(__file__),R/'tools/run_wbuart_present_factor_case_v1.py',R/'tools/run_wbuart_present_factor_feedback_v1.py',R/'tools/pressure_scaled_node_cost_v1.py',R/'tools/present_factor_occupancy_context_v1.py',R/'tools/verify_wbuart_present_factor_events_v1.py',R/'tools/evaluate_external_forecast_case_v1.py',R/'tools/verify_wbuart_present_factor_metrics_v1.py',E/'wbuart_native_present_factor_design_v1_2026-10-20/protocol.json',E/'pressure_scaled_node_cost_contract_v1_2026-10-20/verification.json',E/'wbuart_present_factor_preflight_v1_2026-10-20/verification.json',E/'wbuart_forecasts_v1_2026-10-20/verification.json'];bindings={str(p):sha(p) for p in files};bindings.update(original['bindings'])
 for c in cases:bindings[c['old_specification']]=sha(c['old_specification'])
 mp=D/'manifest.json';mp.write_text(json.dumps({'cases':cases,'bindings':bindings,'quality_gate':original['quality_gate'],'primary_timing_policy':'warm_timing_round_updated','ablation':'warm_timing_frozen','strict_unseen_admitted':False,'native_utility_admitted':False,'timing_scope':'No balanced full paid-time gain claim. Existing inputs, preflight, controls and native labels remain paid dependencies.','commands':[[sys.executable,str(R/'tools/run_wbuart_present_factor_case_v1.py'),str(mp),c['case']] for c in cases],'workers':3,'per_worker_memory_GiB':32,'reuse':'Exactly preflight native_retained/round-updated first-case control+0/.5 pair; all other arms freshly run.'},indent=2)+'\n');print('ALL9_PRESENT_FACTOR_ONLY_TRIAL_FROZEN',flush=True)
 def limit():resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
 def run(c):
  log=D/(c['case'].replace('/','_')+'.log');start=time.perf_counter()
  with log.open('x') as f:p=subprocess.run([sys.executable,str(R/'tools/run_wbuart_present_factor_case_v1.py'),str(mp),c['case']],stdout=f,stderr=subprocess.STDOUT,preexec_fn=limit)
  row={'case':c['case'],'exit_status':p.returncode,'seconds':time.perf_counter()-start,'log':str(log)};print(json.dumps(row),flush=True);return row
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,cases))
 (D/'terminal.json').write_text(json.dumps({'rows':rows,'all_pass':all(r['exit_status']==0 for r in rows)},indent=2)+'\n')
 if not all(r['exit_status']==0 for r in rows):raise RuntimeError('Preserve failing cases; inspect terminal')
 comparisons=[x for c in cases for x in read(Path(c['output'])/'verification.json')['comparisons']];(D/'workflow.json').write_text(json.dumps({'comparisons':comparisons,'manifest':str(mp),'manifest_sha256':sha(mp)},indent=2)+'\n');subprocess.run([sys.executable,str(R/'tools/verify_wbuart_present_factor_metrics_v1.py')],check=True)
if __name__=='__main__':main()
