"""Both frozen initializers use same primary-budget repair; complete audits then scores."""
import json,sys,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from run_external_primary_budget_repair_v1 import predict
from evaluate_external_forecast_case_v1 import evaluate
D=R/'experiments/prospective_external_family_corrected_epoch_predictions_v1_2026-10-19'
def main():
 protocol=json.loads((D/'protocol.json').read_text());assert all(sha(k)==h for k,h in protocol['bindings'].items());c=next(c for c in protocol['cases'] if c['case']==sys.argv[1]);folder=D/c['case'];pred={}
 for init,name in [('raw_min','raw_min_on'),('native_retained','native_retained_on')]:
  out=folder/name;predict(c['endpoint'],out,c['node_base_proof'],c['criticality_directory'],str(Path(c['warm'])/init),'all');proof=out/'complete_event_audit.json';subprocess.run([sys.executable,str(R/'tools/verify_external_primary_budget_repair_events_v1.py'),str(out),c['case'],str(proof)],cwd=R,check=True);pred[name]=dict(frame=str(out/'sketch.json'),proof=str(proof));print('ARM_AUDITED',c['case'],name,flush=True)
 spec=json.loads(Path(c['original_comparison_spec']).read_text());spec.update(case=c['label_case'],source_frame=c['source_frame'],source_proof=c['source_proof'],label_proof=c['label_proof'],label_physical_audit=c['label_physical_audit'],predictions=pred);sp=folder/'comparison_spec.json';sp.write_text(json.dumps(spec,indent=2)+'\n');passed=evaluate(sp,folder/'comparison.json');print('DEVELOPMENT_CASE_GATE',c['case'],passed,flush=True)
if __name__=='__main__':main()
