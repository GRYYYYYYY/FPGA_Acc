"""Fixed first-case control parity and strict-progress complete event qualification."""
import json,subprocess,sys
from pathlib import Path
from run_wbuart_strict_joint_progress_v1 import predict
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_strict_joint_progress_preflight_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);m=json.loads((E/'wbuart_forecasts_v1_2026-10-20/manifest.json').read_text());c=m['cases'][0];case=c['case'];init='native_retained';policy='warm_timing_round_updated';forecast=json.loads((E/'wbuart_forecasts_v1_2026-10-20/verification.json').read_text());old=Path(next(a['output'] for r in forecast['rows'] if r['case']==case for a in r['arms'] if a['initializer']==init and a['timing_policy']==policy));rows=[]
 for strict in [False,True]:
  out=D/('strict' if strict else 'control');predict(c['endpoint'],out,c['node_base_proof'],c['timing_directory'],Path(c['warm_directory'])/init,'all',timing_policy=policy,strict_progress=strict)
  with (D/(out.name+'_audit.log')).open('x') as log:subprocess.run([sys.executable,str(R/'tools/verify_wbuart_strict_joint_progress_v1.py'),str(out),case+'_'+out.name,str(out/'complete_event_audit.json')],stdout=log,stderr=subprocess.STDOUT,check=True)
  if not strict:
   for name in ['initial.json','round0.json','round1.json','sketch.json']:assert json.loads((out/name).read_text())==json.loads((old/name).read_text())
   a,b=[json.loads((p/'receipt.json').read_text()) for p in [out,old]];assert [r['events'] for r in a['rounds']]==[r['events'] for r in b['rounds']]
  rows.append({'strict':strict,'audit':str(out/'complete_event_audit.json'),'audit_sha256':sha(out/'complete_event_audit.json')})
 (D/'verification.json').write_text(json.dumps({'status':'FIRST_CASE_CONTROL_EXACT_PARITY_AND_STRICT_COMPLETE_EVENT_AUDIT_PASS','case':case,'arms':rows,'quality_evaluated':False,'bindings':{str(Path(__file__)):sha(__file__),**{r['audit']:r['audit_sha256'] for r in rows}}},indent=2)+'\n')
if __name__=='__main__':main()
