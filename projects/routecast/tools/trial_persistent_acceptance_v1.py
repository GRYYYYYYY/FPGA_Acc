"""Fresh native/canonical acceptance of persistent-chain outputs, all failures retained."""
import json,sys,subprocess
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/persistent_acceptance_v1_2026-10-09';D.mkdir(exist_ok=False)
mp=R/'tools/persistent_acceptance_manifest_v1.json';m=json.loads(mp.read_text());bindings={str(mp):sha(mp),str(Path(__file__).resolve()):sha(Path(__file__))}
for script in m['scripts']:bindings[script]=sha(script)
rows=[]
for index,script in enumerate(m['scripts']):
 with (D/f'stage_{index:02d}.log').open('x') as log:code=subprocess.run([sys.executable,script],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
 rows.append(dict(index=index,script=script,exit_code=code));(D/'progress.json').write_text(json.dumps(rows,indent=2)+'\n');print(rows[-1],flush=True);assert code==0
quality=[]
for step in range(1,4):
 p=R/f'experiments/persistent_acceptance_v1_step{step}_stage_6_2026-10-09/verification.json';d=json.loads(p.read_text());assert all(sha(p)==h for p,h in d['bindings'].items());bindings.update(d['bindings']);bindings[str(p)]=sha(p);quality.extend(d['rows'])
assert all(sha(p)==h for p,h in bindings.items())
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,quality=quality,scope=m['scope']),indent=2)+'\n');print(quality,flush=True)
