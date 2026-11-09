"""One fixed case, all four arms, complete audits and round0 timing parity."""
import json,subprocess,sys
from pathlib import Path
from pre_route_endpoints import sha
from run_wbuart_fixed_nominal_feedback_v1 import predict
R=Path(__file__).resolve().parents[1]
def main():
 mp=Path(sys.argv[1]).resolve();case=sys.argv[2];m=json.loads(mp.read_text());assert m['schema']=='WBUART_LABEL_FREE_FORECAST_BATCH_V1'
 for n,h in m['bindings'].items():assert sha(n)==h
 c=next(c for c in m['cases'] if c['case']==case);outputs=[]
 for init in m['initializers']:
  for policy in m['timing_policies']:
   out=Path(c['output'])/init/policy;out.parent.mkdir(parents=True,exist_ok=True);predict(c['endpoint'],out,c['node_base_proof'],c['timing_directory'],Path(c['warm_directory'])/init,'all',timing_policy=policy);proof=out/'complete_event_audit.json';log=out.parent/(policy+'_audit.log')
   with log.open('x') as f:rc=subprocess.call([sys.executable,str(R/'tools/verify_wbuart_fixed_nominal_feedback_events_v1.py'),str(out),case+'_'+init+'_'+policy,str(proof)],cwd=R,stdout=f,stderr=subprocess.STDOUT)
   if rc:raise RuntimeError('audit failed; keep fixed case '+case)
   outputs.append({'initializer':init,'timing_policy':policy,'output':str(out),'audit':str(proof),'audit_sha256':sha(proof)})
 parity=[]
 for init in m['initializers']:
  a,b=[Path(r['output']) for r in outputs if r['initializer']==init];ra,rb=[json.loads((d/'receipt.json').read_text()) for d in [a,b]];assert ra['rounds'][0]['events']==rb['rounds'][0]['events'];assert json.loads((a/'round0.json').read_text())==json.loads((b/'round0.json').read_text());assert json.loads((a/'timing_round0.json').read_text())['criticalities']==json.loads((b/'timing_round0.json').read_text())['criticalities'];parity.append({'initializer':init,'round0_equal':True})
 d=Path(c['output']);(d/'verification.json').write_text(json.dumps({'case':case,'arms':outputs,'parity':parity,'new_target_route_labels':False,'bindings':{str(mp):sha(mp),**{r['audit']:r['audit_sha256'] for r in outputs}}},indent=2)+'\n')
if __name__=='__main__':main()
