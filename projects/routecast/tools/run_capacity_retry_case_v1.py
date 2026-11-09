"""Paired off/on production integration, baseline parity before retry arm."""
import json,sys,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from run_external_capacity_retry_v1 import predict
from pre_route_endpoints import sha
D=R/'experiments/prospective_external_family_capacity_retry_v1_2026-10-20';A=R/'experiments/prospective_external_family_fixed_nominal_ablation_v1_2026-10-19'
def read(p):return json.loads(p.read_text())
def main():
 p=read(D/'protocol.json');assert all(sha(k)==h for k,h in p['bindings'].items());c=next(c for c in p['cases'] if c['case']==sys.argv[1]);base=A/c['case']/'native_retained/warm_timing_round_updated'
 for enabled,arm in [(False,'off'),(True,'on')]:
  out=D/c['case']/arm;predict(c['endpoint'],out,c['node_base_proof'],c['criticality_directory'],str(Path(c['warm'])/'native_retained'),'all',timing_policy='warm_timing_round_updated',capacity_retry=enabled)
  subprocess.run([sys.executable,str(R/'tools/verify_external_capacity_retry_events_v1.py'),str(out),c['case'],str(out/'complete_event_audit.json')],cwd=R,check=True)
  if not enabled:
   for name in ['initial.json','round0.json','round1.json','sketch.json']:assert read(out/name)==read(base/name)
   old=read(base/'receipt.json');new=read(out/'receipt.json');assert all(a['events']==b['events'] for a,b in zip(old['rounds'],new['rounds']))
   for ri in [0,1]:assert read(out/f'timing_round{ri}.json')['criticalities']==read(base/f'timing_round{ri}.json')['criticalities']
   (D/c['case']/'off_parity.json').write_text(json.dumps(dict(status='OFF_FULL_STATES_EVENTS_AND_TIMING_EXACT_ARCHIVED_BASELINE'))+'\n')
  print('ARM_AUDITED',c['case'],arm,flush=True)
if __name__=='__main__':main()
