"""One frozen primary-budget-repair case: produce, complete event audit, original evaluation."""
import json,sys,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from run_external_primary_budget_repair_v1 import predict
from evaluate_external_forecast_case_v1 import evaluate
D=R/'experiments/prospective_external_family_primary_budget_repair_v1_2026-10-19'
def main():
 p=json.loads((D/'protocol.json').read_text());assert all(sha(q)==h for q,h in p['bindings'].items());c=next(c for c in p['cases'] if c['case']==sys.argv[1]);out=Path(c['output']);predict(c['endpoint'],out,c['node_base_proof'],c['criticality_directory'],c['warm_directory'],'all');proof=out/'complete_event_audit.json'
 subprocess.run([sys.executable,str(R/'tools/verify_external_primary_budget_repair_events_v1.py'),str(out),c['case'],str(proof)],cwd=R,check=True)
 spec=json.loads(Path(c['original_comparison_spec']).read_text());spec['predictions']['native_retained_on']=dict(frame=str(out/'sketch.json'),proof=str(proof));sp=out/'comparison_spec.json';sp.write_text(json.dumps(spec,indent=2)+'\n');passed=evaluate(sp,out/'comparison.json');print('ORIGINAL_CASE_GATE',passed,flush=True)
if __name__=='__main__':main()
