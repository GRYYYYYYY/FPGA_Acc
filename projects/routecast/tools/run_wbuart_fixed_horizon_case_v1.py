"""All four frozen16round arms and exact original two-round prefix parity."""
import json,sys,subprocess
from pathlib import Path
from run_wbuart_fixed_horizon_v1 import predict
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments'
def read(p):return json.loads(Path(p).read_text())
def main():
 mp=Path(sys.argv[1]);m=read(mp);assert all(sha(p)==h for p,h in m['bindings'].items());c=next(x for x in m['cases'] if x['case']==sys.argv[2]);old=next(r for r in read(E/'wbuart_forecasts_v1_2026-10-20/verification.json')['rows'] if r['case']==c['case']);root=Path(c['output']);root.mkdir(parents=True,exist_ok=True);rows=[]
 for init in ['raw_min','native_retained']:
  for policy in ['warm_timing_frozen','warm_timing_round_updated']:
   reuse=c['case']=='w096/episode_01' and init=='native_retained' and policy=='warm_timing_round_updated';out=E/'wbuart_fixed_horizon_preflight_v1_2026-10-20/model' if reuse else root/init/policy
   if not reuse:
    out.parent.mkdir(parents=True,exist_ok=True);predict(c['endpoint'],out,c['node_base_proof'],c['timing_directory'],Path(c['warm_directory'])/init,'all',timing_policy=policy,round_count=16)
    with (out.parent/(policy+'_audit.log')).open('x') as f:subprocess.run([sys.executable,str(R/'tools/verify_wbuart_fixed_horizon_events_v1.py'),str(out),c['case']+'_'+init+'_'+policy,str(out/'complete_event_audit.json')],stdout=f,stderr=subprocess.STDOUT,check=True)
   proof=read(out/'complete_event_audit.json');assert all(sha(p)==h for p,h in proof['bindings'].items());prev=Path(next(a['output'] for a in old['arms'] if a['initializer']==init and a['timing_policy']==policy))
   for name in ['initial.json','round0.json','round1.json']:assert read(out/name)==read(prev/name)
   a,b=read(out/'receipt.json'),read(prev/'receipt.json');assert [r['events'] for r in a['rounds'][:2]]==[r['events'] for r in b['rounds']]
   for i in [0,1]:assert read(out/f'timing_round{i}.json')['criticalities']==read(prev/f'timing_round{i}.json')['criticalities']
   rows.append({'initializer':init,'timing_policy':policy,'output':str(out),'prefix2_exact_original':True,'audit':str(out/'complete_event_audit.json'),'audit_sha256':sha(out/'complete_event_audit.json')})
 (root/'verification.json').write_text(json.dumps({'case':c['case'],'arms':rows,'bindings':{str(mp):sha(mp),**{r['audit']:r['audit_sha256'] for r in rows}}},indent=2)+'\n')
if __name__=='__main__':main()
