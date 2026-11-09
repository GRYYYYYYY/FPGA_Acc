"""First-case actual Context1/1 parity then0/.5 full price/event/timing qualification."""
import json,subprocess,sys
from pathlib import Path
from run_wbuart_present_factor_feedback_v1 import predict
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_present_factor_preflight_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 D.mkdir(exist_ok=False);design=E/'wbuart_native_present_factor_design_v1_2026-10-20/protocol.json';assert all(sha(p)==h for p,h in read(design)['bindings'].items());c=read(E/'wbuart_forecasts_v1_2026-10-20/manifest.json')['cases'][0];old=Path(next(a['output'] for r in read(E/'wbuart_forecasts_v1_2026-10-20/verification.json')['rows'] if r['case']==c['case'] for a in r['arms'] if a['initializer']=='native_retained' and a['timing_policy']=='warm_timing_round_updated'));rows=[]
 for schedule in ['control','native_first_two']:
  out=D/schedule;predict(c['endpoint'],out,c['node_base_proof'],c['timing_directory'],Path(c['warm_directory'])/'native_retained','all',timing_policy='warm_timing_round_updated',present_schedule=schedule)
  with (D/(schedule+'_audit.log')).open('x') as f:subprocess.run([sys.executable,str(R/'tools/verify_wbuart_present_factor_events_v1.py'),str(out),c['case']+'_'+schedule,str(out/'complete_event_audit.json')],stdout=f,stderr=subprocess.STDOUT,check=True)
  if schedule=='control':
   for name in ['initial.json','round0.json','round1.json','sketch.json']:assert read(out/name)==read(old/name)
   assert [r['events'] for r in read(out/'receipt.json')['rounds']]==[r['events'] for r in read(old/'receipt.json')['rounds']]
   for i in [0,1]:assert read(out/f'timing_round{i}.json')['criticalities']==read(old/f'timing_round{i}.json')['criticalities']
  rows.append({'schedule':schedule,'output':str(out),'audit':str(out/'complete_event_audit.json'),'audit_sha256':sha(out/'complete_event_audit.json')})
 (D/'verification.json').write_text(json.dumps({'status':'FIRST_CASE_FACTOR1_CONTROL_EXACT_PARITY_AND0_HALF_COMPLETE_AUDIT_PASS','rows':rows,'bindings':{str(design):sha(design),str(Path(__file__)):sha(__file__),**{r['audit']:r['audit_sha256'] for r in rows}},'quality_evaluated':False},indent=2)+'\n')
if __name__=='__main__':main()
