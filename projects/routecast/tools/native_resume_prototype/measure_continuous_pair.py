"""External clocks, serial workflow then independent fresh cold; all startup included."""
import json,subprocess,time,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[2];script=Path(__file__).with_name('continuous_cost_trial.py')
out=ROOT/'experiments/native_resume_continuous_pair_2026-10-07';out.mkdir(exist_ok=False)
results=[]
for mode in ('workflow','cold'):
 start=time.perf_counter()
 with (out/f'{mode}.log').open('w') as log:code=subprocess.run([sys.executable,str(script),mode],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=180).returncode
 elapsed=time.perf_counter()-start;results.append(dict(mode=mode,exit_code=code,external_seconds=elapsed,log_sha256=sha(out/f'{mode}.log')))
 (out/'timers.json').write_text(json.dumps(dict(producer_sha256=sha(script),timer_source_sha256=sha(Path(__file__)),rows=results),indent=2)+'\n')
 if code:raise SystemExit(code)
print(results)
