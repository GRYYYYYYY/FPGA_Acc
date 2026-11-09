"""Freeze all9 deterministic pair applications and original-control evaluation."""
import json,subprocess,sys,concurrent.futures,resource
from pathlib import Path
from pre_route_endpoints import sha
from evaluate_external_forecast_case_v1 import evaluate
from external_forecast_metrics_v1 import gate
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_pair_application_trial_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 D.mkdir(exist_ok=False);preflight=E/'wbuart_pair_application_preflight_v1_2026-10-20/model/verification.json';assert read(preflight)['status']=='COMPLETE_PAIR_APPLICATION_XML_FRACTION_AND_ATOMIC_REPLAY_PASS';assert all(sha(p)==h for p,h in read(preflight)['bindings'].items());old=read(E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json');files=[Path(__file__),R/'tools/apply_wbuart_sparse_pairs_v1.py',R/'tools/verify_wbuart_pair_application_v1.py',R/'tools/verify_wbuart_pair_application_metrics_v1.py',preflight,E/'wbuart_sparse_pair_application_design_v1_2026-10-20/protocol.json'];bindings={str(p):sha(p) for p in files};cases=[{'case':c['case'],'old_specification':c['specification'],'old_comparison':c['comparison'],'model_output':str(preflight.parent if c['case']=='w096/episode_01' else D/c['case']/'model')} for c in old['comparisons']]
 for c in cases:bindings[c['old_specification']]=sha(c['old_specification']);bindings[c['old_comparison']]=sha(c['old_comparison'])
 mp=D/'manifest.json';mp.write_text(json.dumps({'cases':cases,'bindings':bindings,'primary_controls':['previous_native','original_two_round_raw_min'],'additional_control':'original_two_round_native_retained','pair_off_ablation':'unchanged warm initial state','scope':'Separate development pair-application trial. Existing two-round failed primary unchanged, no unseen/native utility/full-paid gain claim. Candidate bank generation and audit costs retained.'},indent=2)+'\n');print('ALL9_PAIR_APPLICATION_AND_CONTROLS_FROZEN',flush=True)
 def limit():resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
 def run(c):
  if c['case']=='w096/episode_01':return {'case':c['case'],'exit_status':0,'reused_qualified_preflight':True}
  folder=D/c['case'];folder.mkdir(parents=True)
  with (folder/'run.log').open('x') as f:
   for script,args in [('apply_wbuart_sparse_pairs_v1.py',[c['case'],c['model_output']]),('verify_wbuart_pair_application_v1.py',[c['model_output']])]:
    rc=subprocess.call([sys.executable,str(R/'tools'/script),*args],stdout=f,stderr=subprocess.STDOUT,preexec_fn=limit)
    if rc:return {'case':c['case'],'exit_status':rc}
  return {'case':c['case'],'exit_status':0}
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,cases))
 (D/'terminal.json').write_text(json.dumps({'rows':rows,'all_pass':all(r['exit_status']==0 for r in rows)},indent=2)+'\n');assert all(r['exit_status']==0 for r in rows);comparisons=[]
 for c in cases:
  folder=D/c['case'];folder.mkdir(parents=True,exist_ok=True);s=read(c['old_specification']);s['predictions']['native_retained_on']={'frame':str(Path(c['model_output'])/'sketch.json'),'proof':str(Path(c['model_output'])/'verification.json')};sp=folder/'specification.json';sp.write_text(json.dumps(s,indent=2)+'\n');cp=folder/'comparison.json';evaluate(sp,cp);new=read(cp);oldcomparison=read(c['old_comparison']);additional=gate(new['metrics']['native_retained_on'],oldcomparison['metrics']['native_retained_on']);(folder/'additional_original_model_control.json').write_text(json.dumps({'same_rule_vs_original_two_round_model':additional,'candidate_promoted':False,'scope':'Additional diagnostic control, original quality gate unchanged.'},indent=2)+'\n');comparisons.append({'case':c['case'],'specification':str(sp),'comparison':str(cp)})
 (D/'workflow.json').write_text(json.dumps({'comparisons':comparisons,'manifest':str(mp)},indent=2)+'\n');subprocess.run([sys.executable,str(R/'tools/verify_wbuart_pair_application_metrics_v1.py')],check=True)
if __name__=='__main__':main()
