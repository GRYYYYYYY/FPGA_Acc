"""Recover remaining audits without modifying failed original pipeline evidence."""
import json,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
O=R/'experiments/mmc_observed_round2_full_schedule_v1_2026-10-12';M=O/'model'
bindings=closure([Path(__file__),R/'tools/audit_observed_round2_binding_adapter_v1.py'])
v=json.loads((M/'initial_physical_verification.json').read_text())
assert v['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass']
assert all(sha(p)==h for p,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(M/'initial_physical_verification.json')]=sha(M/'initial_physical_verification.json')
for name,mode,which,dest in [('sketch','physical','sketch','sketch_physical_verification.json'),('events','events','mmc','verification.json')]:
 assert all(sha(p)==h for p,h in bindings.items());tick=time.perf_counter();print('START',name,flush=True)
 with (O/(name+'_audit_recovery_v1.log')).open('x') as log:
  code=subprocess.call([sys.executable,str(R/'tools/audit_observed_round2_binding_adapter_v1.py'),mode,str(M),which,str(M/dest)],stdout=log,stderr=subprocess.STDOUT,cwd=R)
 (O/(name+'_audit_recovery_terminal_v1.json')).write_text(json.dumps(dict(exit_status=code,seconds=time.perf_counter()-tick))+'\n')
 if code:raise SystemExit(code)
 proof=json.loads((M/dest).read_text());assert proof['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'];assert all(sha(p)==h for p,h in proof['bindings'].items());bindings.update(proof['bindings']);bindings[str(M/dest)]=sha(M/dest)
assert all(sha(p)==h for p,h in bindings.items())
(O/'audit_recovery_terminal_v1.json').write_text(json.dumps(dict(exit_status=0,all_three_complete_audits_pass=True,bindings=bindings,original_pipeline_failed=True,scope='Only binding equality assertion replaced by strictly authenticated sole control extension; all original physical and event checks executed.'),indent=2)+'\n');print('RECOVERY COMPLETE',flush=True)
