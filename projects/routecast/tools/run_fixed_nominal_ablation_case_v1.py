"""Four predeclared arms per development case; no case selection."""
import json,sys,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from run_external_fixed_nominal_feedback_v1 import predict
from pre_route_endpoints import sha
D=R/'experiments/prospective_external_family_fixed_nominal_ablation_v1_2026-10-19'
def main():
 p=json.loads((D/'protocol.json').read_text());assert all(sha(k)==h for k,h in p['bindings'].items());c=next(q for q in p['cases'] if q['case']==sys.argv[1]);parity=[]
 for init in ('raw_min','native_retained'):
  outputs=[]
  for policy in ('warm_timing_frozen','warm_timing_round_updated'):
   out=D/c['case']/init/policy;predict(c['endpoint'],out,c['node_base_proof'],c['criticality_directory'],str(Path(c['warm'])/init),'all',timing_policy=policy)
   subprocess.run([sys.executable,str(R/'tools/verify_external_fixed_nominal_feedback_events_v1.py'),str(out),c['case'],str(out/'complete_event_audit.json')],cwd=R,check=True);outputs.append(out);print('ARM_AUDITED',c['case'],init,policy,flush=True)
  a,b=outputs;ra=json.loads((a/'receipt.json').read_text());rb=json.loads((b/'receipt.json').read_text());assert ra['rounds'][0]['events']==rb['rounds'][0]['events'];assert json.loads((a/'round0.json').read_text())==json.loads((b/'round0.json').read_text());ta=json.loads((a/'timing_round0.json').read_text());tb=json.loads((b/'timing_round0.json').read_text());assert ta['criticalities']==tb['criticalities'];parity.append(dict(initializer=init,round0_events_and_state_and_criticality_equal=True,events=len(ra['rounds'][0]['events'])))
 (D/c['case']/'round0_parity.json').write_text(json.dumps(parity,indent=2)+'\n')
if __name__=='__main__':main()
