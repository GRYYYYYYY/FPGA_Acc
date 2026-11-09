"""Reuse admitted cases01/03; recover case02 rounded work cell without native rerun."""
import json,sys,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
names=['recover_mmc_partial_firstpass_admission_v3_2026_10_18.py','verify_mmc_partial_firstpass_comparison_v3_2026_10_18.py','analyze_mmc_partial_firstpass_decision_v3_2026_10_18.py','diagnose_mmc_partial_firstpass_convergence_v2_2026_10_18.py'];core=R/'experiments/native_exact_total_work_core_v2_2026-10-18/verification.json';cv=json.loads(core.read_text());assert cv['status']=='pass' and all(sha(p)==h for p,h in cv['bindings'].items());bindings={**cv['bindings'],str(core):sha(core),**closure([Path(__file__),*[R/'tools'/n for n in names]])}
for case in ['case_01','case_03']:
 p=R/'experiments/mmc_partial_firstpass_recovery_v2_2026-10-18'/case/'verification.json';v=json.loads(p.read_text());assert v['all_native_physical_and_canonical_pass'] and v['native_reruns']==0 and all(sha(p)==h for p,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(p)]=sha(p)
D=R/'experiments/mmc_partial_firstpass_recovery_v3_2026-10-18';D.mkdir();(D/'logs').mkdir()
for case in ['case_01','case_03']:(D/case).symlink_to(R/'experiments/mmc_partial_firstpass_recovery_v2_2026-10-18'/case,target_is_directory=True)
commands=[[sys.executable,str(R/'tools'/names[0]),'case_02'],*[ [sys.executable,str(R/'tools'/n)] for n in names[1:]]]
with (D/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,commands=commands,native_reruns=0,scope='Two existing admitted case audits reused; case02postprocessing only; exact aggregate-derived single rounded heap cell. Original native runs and failed recoveries preserved.'),f,indent=2)
for index,cmd in enumerate(commands):
 print('EXACT RECOVERY STAGE START',index,flush=True)
 with (D/'logs'/(str(index)+'.log')).open('x') as f:code=subprocess.call(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT)
 with (D/(str(index)+'_terminal.json')).open('x') as f:json.dump(dict(command=cmd,exit_code=code),f)
 print('EXACT RECOVERY STAGE TERMINAL',index,code,flush=True)
 if code:raise SystemExit(code)
 if index==0:
  for case in ['case_01','case_02','case_03']:
   p=D/case/'verification.json';v=json.loads(p.read_text());assert v['all_native_physical_and_canonical_pass'] and v['native_reruns']==0;assert all(sha(q)==h for q,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(p)]=sha(p)
   original=R/'experiments/mmc_old_branch_prune_native_v1_2026-10-18'/case;oldp=original/'verification.json';old=json.loads(oldp.read_text());a=next(r for r in v['rows'] if r['arm']=='off');b=next(r for r in old['rows'] if r['arm']=='old_branch_prune');assert sha(D/case/'off/output.route')==sha(original/'old_branch_prune/output.route') and a['wirelength']==b['wirelength'] and a['diagnostic_cpd_ns']==b['diagnostic_cpd_ns']
   for key in ['iterations','total_heap_pushes','total_rerouted_NET_operations','total_rerouted_connection_operations']:assert a['native_work'][key]==b['native_work'][key]
   for x,y in zip(a['native_work']['rows'],b['native_work']['rows']):
    for key in ['iteration','BB_updates','heap_pushes','rerouted_NET_operations','rerouted_connection_operations','overused_RR_nodes']:assert x[key]==y[key]
   bindings[str(oldp)]=sha(oldp)
   for arm in ['off','on']:
    for name in ['native.log','output.route','physical_audit.json']:
     q=D/case/arm/name;bindings[str(q)]=sha(q)
  assert all(sha(q)==h for q,h in bindings.items())
  with (D/'cohort_complete.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,all6_off_on_complete_FULL_physical_canonical_pass=True,all3_flag_off_equal_supported_engine_partial_controls=True,native_reruns=0),f,indent=2)
print('ALL6 EXACT WORK PHYSICAL CANONICAL AND CONVERGENCE AUDITS COMPLETE',flush=True)
