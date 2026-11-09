"""Frozen first-case16round full audit and exact original2round prefix."""
import json,subprocess,sys
from pathlib import Path
from run_wbuart_fixed_horizon_v1 import predict
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_fixed_horizon_preflight_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 D.mkdir(exist_ok=False);design=E/'wbuart_fixed_horizon_design_v1_2026-10-20/protocol.json';assert all(sha(p)==h for p,h in read(design)['bindings'].items());c=read(E/'wbuart_forecasts_v1_2026-10-20/manifest.json')['cases'][0];old=Path(next(a['output'] for r in read(E/'wbuart_forecasts_v1_2026-10-20/verification.json')['rows'] if r['case']==c['case'] for a in r['arms'] if a['initializer']=='native_retained' and a['timing_policy']=='warm_timing_round_updated'));out=D/'model';predict(c['endpoint'],out,c['node_base_proof'],c['timing_directory'],Path(c['warm_directory'])/'native_retained','all',timing_policy='warm_timing_round_updated',round_count=16)
 with (D/'audit.log').open('x') as f:subprocess.run([sys.executable,str(R/'tools/verify_wbuart_fixed_horizon_events_v1.py'),str(out),c['case'],str(out/'complete_event_audit.json')],stdout=f,stderr=subprocess.STDOUT,check=True)
 for name in ['initial.json','round0.json','round1.json','timing_round0.json','timing_round1.json']:
  a,b=read(out/name),read(old/name)
  if name.startswith('timing'):a.pop('source_state');b.pop('source_state')
  assert a==b
 a,b=read(out/'receipt.json'),read(old/'receipt.json');assert [r['events'] for r in a['rounds'][:2]]==[r['events'] for r in b['rounds']]
 (D/'verification.json').write_text(json.dumps({'status':'FIRST16_ROUND_COMPLETE_AUDIT_AND_ORIGINAL_TWO_ROUND_PREFIX_EXACT_PASS','case':c['case'],'output':str(out),'bindings':{str(design):sha(design),str(out/'complete_event_audit.json'):sha(out/'complete_event_audit.json'),str(Path(__file__)):sha(__file__)},'quality_evaluated':False},indent=2)+'\n')
if __name__=='__main__':main()
