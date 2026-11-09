"""Freeze and execute fixed all3 corrected epoch comparison, all failures retained."""
import json,sys,subprocess,concurrent.futures
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
E=R/'experiments';D=E/'prospective_external_family_corrected_epoch_predictions_v1_2026-10-19';I=E/'prospective_external_family_corrected_native_epoch_v1_2026-10-19';N=E/'prospective_external_family_native_shared_sink_native_v1_2026-10-19';OLD=E/'prospective_external_family_supplementary_development_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 dep=[I/'budget_epoch_verification_v1.json',I/'epoch_audit.json',E/'prospective_external_family_corrected_node_bases_v1_2026-10-19/verification.json',N/'verification.json'];bindings={}
 for p in dep:
  proof=read(p);assert all(sha(k)==h for k,h in proof['bindings'].items());bindings[str(p)]=sha(p)
 scripts=[Path(__file__).resolve(),R/'tools/run_external_corrected_epoch_prediction_case_v1.py',R/'tools/run_external_primary_budget_repair_v1.py',R/'tools/verify_external_primary_budget_repair_events_v1.py',R/'tools/evaluate_external_forecast_case_v1.py'];bindings.update(closure(scripts));D.mkdir(exist_ok=False);cases=[]
 for c in read(I/'preparation_terminal.json')['cases']:
  name=c['case'];label=N/name/'cold/native';cases.append(dict(case=name,endpoint=c['endpoint'],warm=c['warm'],node_base_proof=str(E/'prospective_external_family_width_node_bases_v2_2026-10-19/w160/verification.json'),criticality_directory=str(E/'prospective_external_family_frame_timings_v1_2026-10-19'/name),source_frame=str(I/'source_checkpoint/initial.json'),source_proof=str(I/'source_checkpoint/independent_xml_verification_v1.json'),label_proof=str(label/'verification.json'),label_physical_audit=str(label/'physical_audit.json'),label_case=name+'/cold',original_comparison_spec=str(OLD/'specifications'/name/'comparison_spec.json')))
 policy='All3 development cases, both raw_min/native_retained dirty-NET initializers; same existing primary-budget repair producer,10000labels,2rounds,all_NET numeric order,frozen exact initial criticality,original overflow/objective/budget guards. New source prior and matched budgets with corrected cold labels; original full45584 resource/2208 inclusive-bin Spearman/topK gates unchanged. Native-retained compared against previous_native and raw_min under same producer. No score head/threshold tuning, percase winners, old-label replacement, strict unseen or end-to-end speed claims.'
 (D/'protocol.json').write_text(json.dumps(dict(status='FIXED_ALL3_TWO_INITIALIZER_CORRECTED_EPOCH_DEVELOPMENT_PROTOCOL',cases=cases,bindings=bindings,policy=policy,unavailable_cases=read(I/'epoch_audit.json')['unavailable_cases'],supervision=dict(model_delegation_available=False,selected_model='current_session_unchanged',routine_polling='live exec handle and bounded log tails; main model handles failures/results')),indent=2)+'\n')
 def run(c):
  log=D/(c['case'].replace('/','_')+'.log')
  with log.open('x') as f:code=subprocess.run([sys.executable,str(R/'tools/run_external_corrected_epoch_prediction_case_v1.py'),c['case']],cwd=R,stdout=f,stderr=subprocess.STDOUT).returncode
  row=dict(case=c['case'],process_exit=code,log=str(log));rp=D/c['case']/'comparison.json'
  if rp.exists():r=read(rp);row.update(original_case_gate=r['pass_case_gate'],metrics={m:{scope:{k:v[k] for k in ['spearman','top_k_hits','k','universe_size']} for scope,v in scopes.items()} for m,scopes in r['metrics'].items()},checks=r['checks'])
  print(json.dumps(row),flush=True);return row
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,cases))
 bindings={str(D/'protocol.json'):sha(D/'protocol.json'),str(Path(__file__).resolve()):sha(__file__)}
 for c in cases:
  for name in ['comparison.json','comparison_spec.json']:
   p=D/c['case']/name
   if p.exists():bindings[str(p)]=sha(p)
 (D/'quality_summary.json').write_text(json.dumps(dict(status='ALL3_CORRECTED_EPOCH_CASE_PROCESSES_TERMINAL',rows=rows,bindings=bindings,unavailable_cases=read(I/'epoch_audit.json')['unavailable_cases'],all9_availability_pass=False),indent=2)+'\n')
if __name__=='__main__':main()
