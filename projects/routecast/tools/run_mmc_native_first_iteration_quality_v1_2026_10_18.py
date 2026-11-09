"""Original quality metrics only after full prefix physical and input identity checks."""
import json,sys,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure

def main():
 root=R/'experiments/mmc_native_first_iteration_v1_2026-10-18';physical=root/'physical_and_budget_verification_v1.json';identity=root/'input_identity_verification_v1.json';v=json.loads(physical.read_text());i=json.loads(identity.read_text());assert v['status']=='all3_first_iteration_full_XML_physical_identity_and_budget_diagnostics_complete';assert i['status']=='all3_native_capture_inputs_current_endpoint_and_native_manifest_bindings_verified'
 for d in (v,i):assert all(sha(k)==h for k,h in d['bindings'].items())
 out=R/'experiments/mmc_native_first_iteration_quality_v1_2026-10-18';out.mkdir();rows=[];bindings={**closure([Path(__file__)]),str(physical):sha(physical),str(identity):sha(identity)}
 for case in ['case_01','case_02','case_03']:
  old=R/f'experiments/mmc_multiplacement_quality_v1_2026-10-18/{case}/protocol.json';p=json.loads(old.read_text());p['bindings'].update(closure([Path(__file__)]));p['bindings'][str(old)]=sha(old);p['native_prefix_physical_audit']=str(physical);p['native_prefix_input_identity']=str(identity);p['native_prefix_quality_is_diagnostic_only']=True;p['predictions']['native_first_iteration']=str(root/case/'diagnostic_sketch_v1.json');p['primary_candidate']='native_first_iteration';p['evidence_scope']='Fixed native first-iteration diagnostic on3 exposed layouts. Original quality gates and all budget failures retained. Quality pass alone is not full model admission or native utility eligibility.';folder=out/case;folder.mkdir();(folder/'protocol.json').write_text(json.dumps(p,indent=2)+'\n')
  for script in ['evaluate_native_first_iteration_quality_case_v1_2026_10_18.py','verify_native_first_iteration_quality_case_v1_2026_10_18.py']:
   with (folder/f'{script}.log').open('x') as log:code=subprocess.call([sys.executable,str(R/'tools'/script),str(folder)],cwd=R,stdout=log,stderr=subprocess.STDOUT)
   assert code==0,(case,script,code)
  c=json.loads((folder/'comparison.json').read_text());a=json.loads((folder/'verification.json').read_text());assert a['status']=='pass' and a['histogram_rank_topk_mae_checks']==12 and a['primary_gate_pass']==c['primary_gate_pass'];rows.append(dict(case=case,quality_gate_pass=c['primary_gate_pass'],primary_checks=c['primary_checks'],original_V2_budget_gate=next(x['all_original_V2_budgets_pass'] for x in v['cases'] if x['case']==case)));bindings[str(folder/'verification.json')]=sha(folder/'verification.json');print('NATIVE_FIRST_ITERATION_QUALITY',case,c['primary_gate_pass'],flush=True)
 decision=dict(status='all3_fixed_first_iteration_diagnostic_quality_complete',bindings=bindings,cases=rows,all3_original_quality_gates_pass=all(x['quality_gate_pass'] for x in rows),all3_original_V2_budget_gates_pass=all(x['original_V2_budget_gate'] for x in rows),eligible_for_legal_route_commit=False,native_utility_executed=False,accepted_complete_workflow_gain=False);(root/'diagnostic_quality_decision_v1.json').write_text(json.dumps(decision,indent=2)+'\n')
if __name__=='__main__':main()
