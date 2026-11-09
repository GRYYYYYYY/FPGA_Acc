"""Fresh two-arm prospective clocks, same declared input cohort, complete audits."""
import json,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/declared_mux_session_comparison_v1_2026-10-08';D.mkdir(exist_ok=False)
pp=R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json';cases=json.loads(pp.read_text())['cases'];bindings={str(pp):sha(pp),str(Path(__file__)):sha(Path(__file__))}
for c in cases:
 for key in ('old','target','budget'):bindings[c[key]]=sha(c[key])
 old=json.loads(Path(c['old']).read_text());target=json.loads(Path(c['target']).read_text())
 for meta in (old,target):bindings.update({v['path']:v['sha256'] for v in meta['inputs'].values()})
 route=Path(old['inputs']['graph']['path']).with_name('design.route');blif=route.with_name('design.blif');bindings[str(route)]=sha(route);bindings[str(blif)]=sha(blif)
arms=dict(seed=('trial_retained_seed_session_cohort_v2.py','verify_retained_seed_session_cohort_v2.py','trial_retained_seed_session_native_cohort_v2.py','verify_retained_seed_session_native_cohort_v2.py'),cold=('trial_declared_mux_cold_native_cohort_v1.py','verify_declared_mux_cold_native_cohort_v1.py'))
for names in arms.values():
 for name in names:bindings[str(R/'tools'/name)]=sha(R/'tools'/name)
scope='All12 frozen developer moves, same supplied old accepted routes/old-target endpoints/original budgets/RR/original packed netlist-target place. Cold old route available unused; seed starts with cold template and oldroute import. Includes all subprocess startup/shutdown, outputs, copy/seed serialization, all original XML physical/Fraction audits and seed reference certificates. Excludes generating supplied inputs, initial protocol and final top receipt/top verifier. No canonical packedpin reload, original HDL/native STA equivalence, unseen-family or full original-input gain.'
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,arms=arms,scope=scope),indent=2)+'\n')
results={}
for arm,names in arms.items():
 start=time.perf_counter();stages=[]
 for name in names:
  tick=time.perf_counter()
  with (D/f'{arm}_{name}.log').open('w') as log:code=subprocess.run(['python3',str(R/'tools'/name)],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
  stages.append(dict(script=name,exit_code=code,elapsed_seconds=time.perf_counter()-tick));print(arm,stages[-1],flush=True)
  if code:raise RuntimeError('Stage failed: '+name)
 results[arm]=dict(stages=stages,declared_cohort_seconds=time.perf_counter()-start)
 (D/'progress.json').write_text(json.dumps(results,indent=2)+'\n')
assert all(sha(f)==h for f,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,protocol_sha256=sha(D/'protocol.json'),arms=results,full_original_input_workflow_seconds=None,scope=scope),indent=2)+'\n');print(results)
