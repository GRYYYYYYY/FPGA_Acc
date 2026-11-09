"""Freeze and execute all-nine full-control MAP-priority-only trial."""
import json,subprocess,sys,resource,concurrent.futures,time
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_prepared_map_replication_v1_2026-10-20'
def read(p):return json.loads(p.read_text())
def main():
 D.mkdir(exist_ok=False);preflight=read(E/'wbuart_prepared_map_preflight_v1_2026-10-20/verification.json');assert preflight['status']=='FIRST_CASE_PREPARED_H0_MAP_FULL_TRAJECTORY_AND_COMPLETE_AUDIT_PASS';assert all(sha(p)==h for p,h in preflight['bindings'].items());original=read(E/'wbuart_forecasts_v1_2026-10-20/manifest.json');workflow=read(E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json');cases=[]
 for c in original['cases']:
  c=dict(c);c['output']=str(D/c['case']);c['old_specification']=next(r['specification'] for r in workflow['comparisons'] if r['case']==c['case']);c['map_path']=str(next(Path(x['output'])/'allmap.bin' for x in read(E/'wbuart_allnet_map_batch_v1_2026-10-20/target_manifest.json')['cases'] if x['target_case']==c['case'] and x['allmap_enabled']));c['timing_initial']=str(E/'wbuart_frame_timings_v1_2026-10-20'/c['case']/'initial_connection_criticalities.json');c['payload_sha256']=next(x['payload_sha256'] for x in read(E/'wbuart_allnet_map_batch_v1_2026-10-20/independent_matrix_verification_v1.json')['rows'] if x['case']==c['case']);cases.append(c)
 files=[Path(__file__),R/'tools/compiled_prepared_map_tree_v1.py',R/'tools/prepared_map_priority_v1.py',R/'build/map_priority_materialize_v3_2026-10-20/materialize.so',R/'tools/run_wbuart_prepared_map_case_v1.py',R/'tools/run_wbuart_prepared_map_feedback_v1.py',R/'tools/prepared_map_tree_bridge_v1.py',R/'tools/prepared_map_budget_repair_v1.py',R/'tools/verify_wbuart_fixed_nominal_feedback_events_v1.py',R/'tools/evaluate_external_forecast_case_v1.py',R/'tools/verify_wbuart_prepared_map_metrics_v1.py',R/'tools/review_wbuart_prepared_map_trial_v1.py',E/'wbuart_prepared_map_replication_design_v1_2026-10-20/protocol.json',E/'allnet_map_binary_contract_v1_2026-10-20/verification.json',E/'wbuart_prepared_map_preflight_v1_2026-10-20/verification.json',E/'wbuart_forecasts_v1_2026-10-20/verification.json'];bindings={str(p):sha(p) for p in files};bindings.update(original['bindings'])
 for c in cases:
  for key in ['old_specification','map_path','timing_initial']:bindings[c[key]]=sha(c[key])
 mp=D/'manifest.json';mp.write_text(json.dumps({'cases':cases,'bindings':bindings,'quality_gate':original['quality_gate'],'primary_timing_policy':'warm_timing_round_updated','ablation':'warm_timing_frozen','strict_unseen_admitted':False,'native_utility_admitted':False,'timing_scope':'No balanced full paid-time gain claim. Existing inputs, preflight, controls and native labels remain paid dependencies.','commands':[[sys.executable,str(R/'tools/run_wbuart_prepared_map_case_v1.py'),str(mp),c['case']] for c in cases],'workers':9,'per_worker_memory_GiB':8,'reuse':'Exactly preflight native_retained/round-updated first-case H0+MAP pair; all other arms freshly run.'},indent=2)+'\n');print('ALL9_PREPARED_IMPLEMENTATION_REPLICATION_FROZEN',flush=True)
 def limit():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
 def run(c):
  log=D/(c['case'].replace('/','_')+'.log');start=time.perf_counter()
  with log.open('x') as f:p=subprocess.run([sys.executable,str(R/'tools/run_wbuart_prepared_map_case_v1.py'),str(mp),c['case']],stdout=f,stderr=subprocess.STDOUT,preexec_fn=limit)
  row={'case':c['case'],'exit_status':p.returncode,'seconds':time.perf_counter()-start,'log':str(log)};print(json.dumps(row),flush=True);return row
 with concurrent.futures.ThreadPoolExecutor(max_workers=9) as pool:rows=list(pool.map(run,cases))
 (D/'terminal.json').write_text(json.dumps({'rows':rows,'all_pass':all(r['exit_status']==0 for r in rows)},indent=2)+'\n')
 if not all(r['exit_status']==0 for r in rows):raise RuntimeError('Preserve failing cases; inspect terminal')
 comparisons=[x for c in cases for x in read(Path(c['output'])/'verification.json')['comparisons']];(D/'workflow.json').write_text(json.dumps({'comparisons':comparisons,'manifest':str(mp),'manifest_sha256':sha(mp)},indent=2)+'\n');subprocess.run([sys.executable,str(R/'tools/verify_wbuart_prepared_map_metrics_v1.py')],check=True);subprocess.run([sys.executable,str(R/'tools/review_wbuart_prepared_map_trial_v1.py')],check=True)
if __name__=='__main__':main()
