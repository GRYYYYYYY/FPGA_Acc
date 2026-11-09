"""Four fixed pairs alternating order; all observations retained."""
import json,subprocess,time,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[2];script=Path(__file__).with_name('precritical_repeat_trial.py')
out=ROOT/'experiments/native_resume_precritical_repeats_2026-10-07';out.mkdir(exist_ok=False)
order=[(f'p{i}',mode) for i in range(4) for mode in (('workflow','cold') if i%2==0 else ('cold','workflow'))]
protocol=dict(producer_sha256=sha(script),timer_source_sha256=sha(Path(__file__)),order=order,scope='Fixed4 paired serial repetitions; alternating order, OS caches not reset, prepared-input scope; no parameter/QoR tuning, all logs and failures retained')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');results=[]
for tag,mode in order:
 start=time.perf_counter();log=out/f'{tag}_{mode}.log'
 with log.open('w') as stream:code=subprocess.run([sys.executable,str(script),mode,tag],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,timeout=180).returncode
 elapsed=time.perf_counter()-start;row=dict(pair=tag,mode=mode,exit_code=code,external_seconds=elapsed,log_sha256=sha(log));results.append(row)
 (out/'timers.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=results),indent=2)+'\n');print(row,flush=True)
 if code:raise SystemExit(code)
