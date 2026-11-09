"""Full-control single-factor native MAP priority case with original quality comparisons."""
import json,sys,subprocess
from pathlib import Path
from run_wbuart_map_priority_feedback_v1 import predict
from bound_allnet_map_query_v2 import Query
from pre_route_endpoints import sha
from evaluate_external_forecast_case_v1 import evaluate
R=Path(__file__).resolve().parents[1];E=R/'experiments'
def read(p):return json.loads(Path(p).read_text())
def main():
 mp=Path(sys.argv[1]);m=read(mp);assert all(sha(p)==h for p,h in m['bindings'].items());c=next(c for c in m['cases'] if c['case']==sys.argv[2]);root=Path(c['output']);root.mkdir(parents=True,exist_ok=True);old=next(r for r in read(E/'wbuart_forecasts_v1_2026-10-20/verification.json')['rows'] if r['case']==c['case']);outputs=[]; query=Query(c['map_path'],c['endpoint'],c['timing_initial'],c['payload_sha256'])
 for init in ['raw_min','native_retained']:
  for policy in ['warm_timing_frozen','warm_timing_round_updated']:
   paths={}
   for strict in [False,True]:
    reuse=c['case']=='w096/episode_01' and init=='native_retained' and policy=='warm_timing_round_updated';out=E/('wbuart_map_priority_nonzero_v1_2026-10-20' if strict else 'wbuart_map_priority_control_v1_2026-10-20')/('MAP' if strict else 'H0') if reuse else root/init/policy/('MAP' if strict else 'H0');paths[strict]=out
    if not reuse:
     out.parent.mkdir(parents=True,exist_ok=True);predict(c['endpoint'],out,c['node_base_proof'],c['timing_directory'],Path(c['warm_directory'])/init,'all',timing_policy=policy,map_query=query,priority_mode='MAP' if strict else 'H0')
     with (out.parent/(out.name+'_audit.log')).open('x') as log:subprocess.run([sys.executable,str(R/'tools/verify_wbuart_fixed_nominal_feedback_events_v1.py'),str(out),c['case']+'_'+init+'_'+policy+'_'+out.name,str(out/'complete_event_audit.json')],stdout=log,stderr=subprocess.STDOUT,check=True)
    proof=read(out/'complete_event_audit.json');assert all(sha(p)==h for p,h in proof['bindings'].items())
    if not strict:
     prev=Path(next(a['output'] for a in old['arms'] if a['initializer']==init and a['timing_policy']==policy))
     for name in ['initial.json','round0.json','round1.json','sketch.json','primary_budget_repairs.json']:assert read(out/name)==read(prev/name)
     assert [r['events'] for r in read(out/'receipt.json')['rounds']]==[r['events'] for r in read(prev/'receipt.json')['rounds']]
     for i in [0,1]:assert read(out/f'timing_round{i}.json')['criticalities']==read(prev/f'timing_round{i}.json')['criticalities']
   outputs.append({'initializer':init,'timing_policy':policy,'candidate_output':str(paths[True]),'control_output':str(paths[False]),'control_parity':True})
 query.close()
 comparisons=[]
 for policy in ['warm_timing_frozen','warm_timing_round_updated']:
  spec=read(c['old_specification']);spec['predictions']={name:{'frame':str(Path(next(a['candidate_output'] for a in outputs if a['initializer']==init and a['timing_policy']==policy))/'sketch.json'),'proof':str(Path(next(a['candidate_output'] for a in outputs if a['initializer']==init and a['timing_policy']==policy))/'complete_event_audit.json')} for name,init in [('native_retained_on','native_retained'),('raw_min_on','raw_min')]};sp=root/(policy+'_specification.json');sp.write_text(json.dumps(spec,indent=2)+'\n');cp=root/(policy+'_comparison.json');evaluate(sp,cp);comparisons.append({'case':c['case'],'timing_policy':policy,'specification':str(sp),'comparison':str(cp)})
 (root/'verification.json').write_text(json.dumps({'case':c['case'],'arms':outputs,'comparisons':comparisons,'bindings':{str(mp):sha(mp)}},indent=2)+'\n')
if __name__=='__main__':main()
