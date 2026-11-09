"""Exactly three fixed candidate native runs; archived controls are not rerun."""
import json,sys,subprocess,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from versioned_digest_cache_v1 import Cache

def main():
 seeds=R/'experiments/mmc_terminal_native_seed_inputs_v1_2026-10-18'
 admission=seeds/'seed_admission_verification_v1.json';settings=seeds/'native_settings_bindings_v1.json';protocol=seeds/'protocol.json'
 a=json.loads(admission.read_text());s=json.loads(settings.read_text());p=json.loads(protocol.read_text())
 assert a['status']=='pass' and a['all3_seeds_independently_admitted'] and p['native_settings']==s['settings']
 controls=R/'experiments/mmc_v2_native_utility_v1_2026-10-18'
 cc=controls/'cohort_complete.json';cw=controls/'independent_wire_work_verification_v1.json'
 c=json.loads(cc.read_text());w=json.loads(cw.read_text());assert c['all15_native_FULL_physical_and_canonical_semantic_pass'] and w['all15_original_XML_wire_and_log_work_counters_independently_equal']
 exact=R/'experiments/native_exact_total_work_core_v2_2026-10-18/verification.json';e=json.loads(exact.read_text());assert e['status']=='pass' and e['all6_both_parsers_every_integer_row_equal'] and e['both_parsers_reject_all_negative_fixtures']
 script=R/'tools/run_mmc_terminal_native_utility_case_v1_2026_10_18.py'
 bindings={**a['bindings'],**s['bindings'],**c['bindings'],**w['bindings'],**e['bindings'],**closure([Path(__file__),script])}
 for path in [admission,settings,protocol,cc,cw,exact]:bindings[str(path)]=sha(path)
 cache=Cache()
 with cache.installed():assert all(sha(path)==h for path,h in bindings.items())
 d=R/'experiments/mmc_terminal_native_utility_v1_2026-10-18';d.mkdir();(d/'logs').mkdir()
 with (d/'protocol.json').open('x') as stream:
  json.dump(dict(bindings=bindings,frozen_seed_protocol=str(protocol),candidate_case_order=['case_01','case_02','case_03'],max_parallel_cases=3,native_settings=p['native_settings'],controls=p['controls'],utility_screen=p['utility_screen'],monitoring='long-run-supervision; no supported luna delegation interface. Single launcher owner, live case/native PIDs and terminal receipts retained. No automatic restart, no elapsed-time cancellation.',scope='Exactly3 new candidate runs under frozen settings. Archived controls authenticated, not re-executed; no balanced end-to-end clock or forecast promotion.'),stream,indent=2)
 def run(case):
  tick=time.perf_counter();print('CANDIDATE CASE START',case,flush=True)
  with (d/'logs'/(case+'.log')).open('x') as log:
   process=subprocess.Popen([sys.executable,str(script),case],cwd=R,stdout=log,stderr=subprocess.STDOUT)
   with (d/'logs'/(case+'.started.json')).open('x') as stream:json.dump(dict(case=case,pid=process.pid,script=str(script)),stream,indent=2)
   code=process.wait()
  result=dict(case=case,exit_code=code,case_process_seconds=time.perf_counter()-tick)
  print('CANDIDATE CASE TERMINAL',json.dumps(result),flush=True);return result
 stages=[]
 with ThreadPoolExecutor(max_workers=3) as pool:
  for future in as_completed([pool.submit(run,case) for case in ['case_01','case_02','case_03']]):
   stages.append(future.result());(d/'stage_status.json').write_text(json.dumps(stages,indent=2))
 assert len(stages)==3 and all(row['exit_code']==0 for row in stages), 'Preserve completed native artifacts; recover postprocessing only, never restart native for an audit error'
 rows=[]
 with cache.installed():
  for case in ['case_01','case_02','case_03']:
   path=d/case/'verification.json';v=json.loads(path.read_text());assert v['all_native_physical_and_canonical_pass'] and len(v['rows'])==1
   row=v['rows'][0];assert row['arm']=='candidate' and row['independent_original_XML_wire_and_exact_work_pass']
   bindings.update(v['bindings']);bindings[str(path)]=sha(path);rows.append(dict(case=case,row=row))
  assert all(sha(path)==h for path,h in bindings.items())
  with (d/'cohort_complete.json').open('x') as stream:json.dump(dict(status='pass',bindings=bindings,rows=stages,all3_native_FULL_physical_canonical_and_independent_wire_work_pass=True,scope='All3fixed candidate native outcomes admitted. Exact work and native wire/diagnosticCPD screening still separate from full-flow timing/generalization.'),stream,indent=2)
  decisions=[]
  for item in rows:
   case=item['case'];candidate=item['row'];path=controls/case/'verification.json';v=json.loads(path.read_text());assert v['all_native_physical_and_canonical_pass']
   arms={row['arm']:row for row in v['rows']};assert set(p['controls'])==set(arms)
   checks=[]
   for control in p['controls']:
    ref=arms[control]
    checks.append(dict(control=control,heap_pushes_strictly_lower=candidate['native_work']['total_heap_pushes']<ref['native_work']['total_heap_pushes'],wirelength_nonworse=candidate['wirelength']<=ref['wirelength'],diagnostic_CPD_nonworse=candidate['diagnostic_cpd_ns']<=ref['diagnostic_cpd_ns']))
   result=dict(case=case,candidate={k:candidate[k] for k in ['iterations','wirelength','diagnostic_cpd_ns','native_work','canonical']},checks=checks,pass_frozen_utility_screen=all(all(check[k] for k in ['heap_pushes_strictly_lower','wirelength_nonworse','diagnostic_CPD_nonworse']) for check in checks))
   decisions.append(result);print('FROZEN UTILITY SCREEN',case,result['pass_frozen_utility_screen'],flush=True)
  assert all(sha(path)==h for path,h in bindings.items())
  with (d/'research_decision_v1.json').open('x') as stream:json.dump(dict(status='all3_native_candidates_independently_admitted_and_screened',bindings={**bindings,str(d/'cohort_complete.json'):sha(d/'cohort_complete.json')},cases=decisions,all3_frozen_utility_screens_pass=all(row['pass_frozen_utility_screen'] for row in decisions),scope='Fixed development cohort and5archived controls percase. Parallel component times exclude cached prefix/export/model/other costs. No end-to-end speedup, forecast promotion, heldout-family, fullSTA or hardware claim.'),stream,indent=2)
 print('ALL3 TERMINAL CANDIDATE NATIVE RUNS SCREENED',flush=True)

if __name__=='__main__':main()
