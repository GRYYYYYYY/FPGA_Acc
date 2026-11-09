"""Fixed all12 development moves, alternating within-case routing order."""
import json,subprocess,time,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[2];script=Path(__file__).with_name('cohort_singlepass_floor_trial.py')
out=ROOT/'experiments/native_resume_singlepass_floor_controls_2026-10-07';out.mkdir(exist_ok=False)
cases=[(16,1),(32,3)]
order=[(w,i,mode) for n,(w,i) in enumerate(cases) for mode in (('workflow','cold') if n%2==0 else ('cold','workflow'))]
source_protocol=ROOT/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json';source=json.loads(source_protocol.read_text())
inputs={path:digest for case in source['cases'] for path,digest in case['inputs'].items()}
assert all(sha(p)==h for p,h in inputs.items())
protocol=dict(source_protocol_sha256=sha(source_protocol),producer_sha256=sha(script),timer_source_sha256=sha(Path(__file__)),order=order,inputs=inputs,scope='Fixed2 diagnostic controls from existing development moves, includes previously skipped estimator cases. One attempt precritical old-state release fixed rule; fresh paired same-index-corrected initial-tolerance1.01 wholeNET-trigger single-pass independent-floor cold. Alternating order, no target QoR threshold tuning, all failures and timings retained; prepared-input scope, not heldout')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');results=[]
for w,i,mode in order:
 start=time.perf_counter();log=out/f'w{w}_m{i}_{mode}.log'
 with log.open('w') as stream:
  try:code=subprocess.run([sys.executable,str(script),mode,str(w),str(i)],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,timeout=180).returncode
  except subprocess.TimeoutExpired:code=124
 row=dict(width=w,index=i,mode=mode,exit_code=code,external_seconds=time.perf_counter()-start,log_sha256=sha(log));results.append(row)
 (out/'timers.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=results),indent=2)+'\n');print(row,flush=True)
assert all(sha(p)==h for p,h in inputs.items())
