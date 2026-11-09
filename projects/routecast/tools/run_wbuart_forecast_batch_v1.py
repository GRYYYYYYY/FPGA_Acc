"""Frozen nine-case label-free prediction/ablation phase, preserve all outcomes."""
import concurrent.futures,hashlib,json,resource,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_forecasts_v1_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);preflight=E/'wbuart_real_feedback_pipeline_v3_2026-10-20/verification.json';p=json.loads(preflight.read_text());assert len(p['rows'])==4 and all(r['round0_events_state_and_criticalities_equal'] for r in p['parity'])
 for n,h in p['bindings'].items():assert sha(Path(n))==h
 script=R/'tools/run_wbuart_forecast_case_v1.py';files=[Path(__file__),script,R/'tools/run_wbuart_fixed_nominal_feedback_v1.py',R/'tools/verify_wbuart_fixed_nominal_feedback_events_v1.py',preflight,E/'wbuart_quality_domains_v1_2026-10-20/verification.json',E/'wbuart_quality_domains_v1_2026-10-20/independent_verification_v1.json'];bindings={str(p):sha(p) for p in files};cases=[]
 for w in [96,128,160]:
  for i in [1,2,3]:
   case=f'w{w:03d}/episode_{i:02d}';ep=E/'wbuart_width_frames_v2_2026-10-20'/case/'routing_endpoints.json';node=E/'wbuart_node_bases_v1_2026-10-20'/f'w{w:03d}/verification.json';td=E/'wbuart_frame_timings_v1_2026-10-20'/case;warm=E/'wbuart_warm_inputs_v1_2026-10-20'/case;reuse=case=='w096/episode_01';cases.append({'case':case,'endpoint':str(ep),'node_base_proof':str(node),'timing_directory':str(td),'warm_directory':str(warm),'output':str(D/case),'reuse_preflight_arms':p['rows'] if reuse else None})
   for path in [ep,node,td/'verification.json',*[warm/m/'verification.json' for m in ['raw_min','native_retained']]]:bindings[str(path)]=sha(path)
 manifest={'schema':'WBUART_LABEL_FREE_FORECAST_BATCH_V1','cases':cases,'bindings':bindings,'initializers':['raw_min','native_retained'],'timing_policies':['warm_timing_frozen','warm_timing_round_updated'],'primary_timing_policy':'warm_timing_round_updated','primary_selection_reason':'Existing round-updated fixed-nominal formulation; frozen before any new native target labels, never choose per case or internal overflow result. Frozen policy reported as ablation only.','rounds':2,'primary_repair_labels':10000,'scheduling':'all NETs every round','source_history':'OFF','source_budget_price_objective_guards':'Existing fixed policies unchanged; exact own-epoch input proofs required.','quality_gate':'Original full-domain four-metric gate every one of9 cases, candidate native_retained_on versus previous_native and raw_min_on, nonregress all4 and strictly improve≥1 per control, Spearman eps1e-12, exact hit counts; undefined/null or missing case fails, no selective averages or replacement.','scope':'Prediction+timing ablation phase only. Complete target-native/utility/full-paid-time executable protocol still not admitted. No native target routing in this driver. Historical source/input/preflight costs remain paid dependencies, no component-time gain claim.','strict_unseen_admitted':False};mp=D/'manifest.json';mp.write_text(json.dumps(manifest,indent=2)+'\n');print('ALL9_FORECAST_CONFIGURATION_FROZEN',flush=True)
 def limit():resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
 def run(c):
  if c['reuse_preflight_arms']:return {'case':c['case'],'exit_status':0,'reused_preflight':True,'arms':c['reuse_preflight_arms'],'preflight':str(preflight)}
  out=Path(c['output']);out.mkdir(parents=True);start=time.perf_counter()
  with (out/'case.log').open('x') as f:rc=subprocess.call([sys.executable,str(script),str(mp),c['case']],cwd=R,stdout=f,stderr=subprocess.STDOUT,preexec_fn=limit)
  row={'case':c['case'],'exit_status':rc,'seconds':time.perf_counter()-start,'verification':str(out/'verification.json'),'reused_preflight':False};(out/'terminal.json').write_text(json.dumps(row,indent=2)+'\n');print(json.dumps(row),flush=True);return row
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,cases))
 (D/'terminal.json').write_text(json.dumps({'status':'ALL9_LABEL_FREE_FORECAST_CASE_WORKERS_TERMINAL','rows':rows,'all_pass':all(r['exit_status']==0 for r in rows),'new_target_route_labels':False,'complete_native_utility_workflow_admitted':False,'bindings':{str(mp):sha(mp)}},indent=2)+'\n')
if __name__=='__main__':main()
