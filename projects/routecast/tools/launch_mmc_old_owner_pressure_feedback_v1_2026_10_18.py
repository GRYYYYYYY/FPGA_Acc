"""Run fixed initial-overuse owner context, then final/full-event independent audits."""
import json,sys,subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
contract=R/'experiments/mmc_old_owner_pressure_feedback_source_contract_v1_2026-10-18/verification.json';sc=json.loads(contract.read_text());assert sc['status']=='pass' and all(sha(p)==h for p,h in sc['bindings'].items());selection=R/'experiments/mmc_old_owner_pressure_context_v1_2026-10-18/independent_selection_verification_v1.json';v=json.loads(selection.read_text());assert v['all3_pressure_sets_and_old_owner_NET_contexts_independently_equal'] and all(sha(p)==h for p,h in v['bindings'].items());names=['run_mmc_old_owner_pressure_feedback_v1_2026_10_18.py','audit_mmc_old_owner_pressure_feedback_case_v1_2026_10_18.py'];bindings={**sc['bindings'],**v['bindings'],str(contract):sha(contract),str(selection):sha(selection),**closure([Path(__file__),*[R/'tools'/n for n in names]])};D=R/'experiments/mmc_old_owner_pressure_feedback_launch_v1_2026-10-18';D.mkdir();(D/'logs').mkdir();O=R/'experiments/mmc_old_owner_pressure_feedback_v1_2026-10-18'
with (D/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,cases=['case_01','case_02','case_03'],fixed_context_NET_counts=[84,89,229],expected_events=[168,178,458],rounds=2,quality_plan=dict(primary_label='original_cold_native',supplemental_labels=['partial_seed_default','partial_seed_firstpass_preserve'],existing_forecasts=['raw_min_off','raw_min_on','native_retained_off','native_retained_on','previous_native'],candidate='native_retained_owner_pressure_on',fixed_controls=['native_retained_on','raw_min_on','previous_native'],domains=['concrete','spatial'],expected_full_domain_metric_vectors=108),scope='Scope-only fixed exposed mechanism ablation. Allfinal and allevent audits mandatory before any quality evaluation. Initial models/budgets/timing unchanged; cached inputs, no fresh full-flow timing gain or heldout/hardware claim.'),f,indent=2)
cmd=[sys.executable,str(R/'tools'/names[0])];print('OWNER PRESSURE MODEL START',flush=True)
with (D/'logs/model.log').open('x') as f:code=subprocess.call(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT)
with (D/'model_terminal.json').open('x') as f:json.dump(dict(command=cmd,exit_code=code),f)
print('OWNER PRESSURE MODEL TERMINAL',code,flush=True)
if code:raise SystemExit(code)
r=json.loads((O/'receipt.json').read_text());assert [x['case'] for x in r['rows']]==['case_01','case_02','case_03'] and [x['events'] for x in r['rows']]==[168,178,458]
def audit(case):
 print('OWNER PRESSURE AUDIT START',case,flush=True)
 cmd=[sys.executable,str(R/'tools'/names[1]),case]
 with (D/'logs'/(case+'_audits.log')).open('x') as f:code=subprocess.call(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT)
 result=dict(case=case,exit_code=code);print('OWNER PRESSURE AUDIT TERMINAL',result,flush=True);return result
rows=[]
with ThreadPoolExecutor(max_workers=3) as pool:
 for f in as_completed([pool.submit(audit,c) for c in ['case_01','case_02','case_03']]):rows.append(f.result());(D/'audit_stages.json').write_text(json.dumps(rows,indent=2))
assert all(x['exit_code']==0 for x in rows)
for case in ['case_01','case_02','case_03']:
 p=O/case/'audits/verification.json';a=json.loads(p.read_text());assert a['both_final_and_all_context_events_pass'] and a['initial_frame_byte_equal_independently_audited_retained_off'];bindings.update(a['bindings']);bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items())
with (O/'cohort_complete.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,rows=rows,all3_final_and_every_event_independently_admitted=True,quality_and_cost_benefit_pending=True),f,indent=2)
print('ALL3OWNER PRESSURE FINAL AND EVERYEVENT VERIFIED',flush=True)
