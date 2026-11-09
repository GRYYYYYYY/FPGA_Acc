"""Admit frozen inputs, run the paired cohort, then independently audit all outputs."""
import json,sys,subprocess,datetime
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
fp=R/'experiments/mmc_partial_firstpass_ablation_frozen_v1_2026-10-18.json';frozen=json.loads(fp.read_text());assert frozen['status']=='frozen_before_partial_cohort';assert all(sha(p)==h for p,h in frozen['bindings'].items())
bindings={**frozen['bindings'],str(fp):sha(fp),**closure([Path(__file__)])}
for mode in ['off','on']:
 p=R/('experiments/mmc_partial_firstpass_equivalence_'+mode+'_v1_2026-10-18/equivalence_verification_v1.json');v=json.loads(p.read_text());assert v['status']=='pass' and v['no_seed_and_complete_NET_seed_old_behavior_equal'];assert all(sha(q)==h for q,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(p)]=sha(p)
D=R/'experiments/mmc_partial_firstpass_launch_v1_2026-10-18';D.mkdir()
commands=[[sys.executable,str(R/'tools'/name)] for name in ['run_mmc_partial_firstpass_native_cohort_v1_2026_10_18.py','verify_mmc_partial_firstpass_comparison_v1_2026_10_18.py']]
with (D/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,commands=commands,admitted_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Frozen matched partial firstpass cohort and independent wire/work; no automatic gain or promotion assertion.'),f,indent=2)
for index,cmd in enumerate(commands):
 print('FIRSTPASS STAGE START',index,flush=True)
 with (D/(str(index)+'.log')).open('x') as log:code=subprocess.call(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT)
 with (D/(str(index)+'_terminal.json')).open('x') as f:json.dump(dict(command=cmd,exit_code=code),f)
 print('FIRSTPASS STAGE TERMINAL',index,code,flush=True)
 if code:raise SystemExit(code)
print('FIRSTPASS PAIRED COHORT AND INDEPENDENT AUDIT TERMINAL PASS',flush=True)
