"""Frozen single-step fresh history+proof workflow outer timer."""
import json,subprocess,sys,time
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/history_step3_v1_2026-10-09';D.mkdir(exist_ok=False)
manifest=R/'tools/history_step3_manifest_v1.json';plan=json.loads(manifest.read_text())
bindings={str(manifest):sha(manifest),str(Path(__file__).resolve()):sha(Path(__file__))}
for script in plan['scripts']:bindings[script]=sha(script)
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,manifest=plan),indent=2)+'\n')
rows=[];start=time.perf_counter()
for index,script in enumerate(plan['scripts']):
 tick=time.perf_counter()
 with (D/f'stage_{index:02d}.log').open('x') as log:
  code=subprocess.run([sys.executable,script],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
 rows.append(dict(index=index,script=script,exit_code=code,seconds=time.perf_counter()-tick))
 (D/'progress.json').write_text(json.dumps(rows,indent=2)+'\n');print(rows[-1],flush=True)
 if code:raise RuntimeError('Failed stage '+str(index))
elapsed=time.perf_counter()-start
quality=R/'experiments/history_step3_v1_stage_6_2026-10-09/verification.json'
q=json.loads(quality.read_text());assert all(sha(p)==h for p,h in q['bindings'].items())
assert all(sha(p)==h for p,h in bindings.items())
for p in D.iterdir():
 if p.is_file():bindings[str(p)]=sha(p)
bindings[str(quality)]=sha(quality)
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,quality=q['rows'],workflow_seconds=elapsed,scope=plan['scope']),indent=2)+'\n')
print(dict(workflow_seconds=elapsed,quality=q['rows']),flush=True)
