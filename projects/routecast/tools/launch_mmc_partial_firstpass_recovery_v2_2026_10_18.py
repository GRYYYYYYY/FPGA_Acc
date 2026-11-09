"""Recover completed native outputs, preserving failed v1 harness provenance."""
import json,sys,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
old=R/'experiments/mmc_partial_firstpass_native_v1_2026-10-18';bindings=closure([Path(__file__)])
for case in ['case_01','case_02','case_03']:
 vp=old/case/'verification.json';v=json.loads(vp.read_text());assert not v['all_native_physical_and_canonical_pass'];assert all(sha(p)==h for p,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(vp)]=sha(vp)
 assert next(r for r in v['rows'] if r['arm']=='off')['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS'
 on=next(r for r in v['rows'] if r['arm']=='on');assert on['exit_status']==0 and on['error']=='AssertionError()'
 for arm in ['off','on']:
  p=old/case/arm/'terminal.json';t=json.loads(p.read_text());assert t['exit_status']==0 and not t['native_timeout'];bindings[str(p)]=sha(p)
D=R/'experiments/mmc_partial_firstpass_recovery_launch_v2_2026-10-18';D.mkdir();names=['recover_mmc_partial_firstpass_cohort_v2_2026_10_18.py','verify_mmc_partial_firstpass_comparison_v2_2026_10_18.py','analyze_mmc_partial_firstpass_decision_v2_2026_10_18.py'];commands=[[sys.executable,str(R/'tools'/name)] for name in names]
for name in names:bindings[str(R/'tools'/name)]=sha(R/'tools'/name)
with (D/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,commands=commands,native_reruns=0,scope='Existing completed six native runs only; v1eligible-pending postprocessor assertion fixed through partition-derived counts, no gate relaxed.'),f,indent=2)
for index,cmd in enumerate(commands):
 print('RECOVERY STAGE START',index,flush=True)
 with (D/(str(index)+'.log')).open('x') as log:code=subprocess.call(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT)
 with (D/(str(index)+'_terminal.json')).open('x') as f:json.dump(dict(command=cmd,exit_code=code),f)
 print('RECOVERY STAGE TERMINAL',index,code,flush=True)
 if code:raise SystemExit(code)
print('RECOVERY ADMISSION AND INDEPENDENT COMPARISON TERMINAL PASS',flush=True)
