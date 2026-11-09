"""Fresh actual replay of all archived production phases, timed across subprocesses."""
import json,subprocess,sys,time
from pathlib import Path
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];D=R/'experiments/adder_online_production_cost_replay_v2_2026-10-09';D.mkdir(exist_ok=False);mp=R/'tools/online_cost_replay_manifest_v2.json';manifest=json.loads(mp.read_text());bindings={**closure([Path(__file__),*[R/'tools'/s['script'] for s in manifest['stages']]]),str(mp):sha(mp)};(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,manifest=manifest,scope='Wall clock from before first child through final child includes startup, all search/independent proofs/output writes/serialization/native/canonical. Protocol setup/final receipt rehash and supplied inputs production excluded. No independent paired cold arm.'),indent=2)+'\n');start=time.perf_counter();rows=[]
for i,stage in enumerate(manifest['stages']):
 tick=time.perf_counter()
 with (D/f'stage_{i}.log').open('x') as log:code=subprocess.run([sys.executable,str(R/'tools'/stage['script'])],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
 row=dict(stage=i,script=stage['script'],original=stage['original'],exit_code=code,wall_seconds=time.perf_counter()-tick);rows.append(row);(D/'progress.json').write_text(json.dumps(rows,indent=2)+'\n');print(row,flush=True)
 if code:break
elapsed=time.perf_counter()-start;assert all(sha(p)==h for p,h in bindings.items());success=len(rows)==len(manifest['stages']) and all(r['exit_code']==0 for r in rows);quality=R/'experiments'/manifest['mapping']['adder_online_full_native_quality_v1_2026-10-09']/'verification.json'
if success:
 q=json.loads(quality.read_text());assert all(sha(p)==h for p,h in q['bindings'].items());assert len(q['rows'])==1 and q['rows'][0]['step']==3 and q['rows'][0]['wirelength']==2609 and q['rows'][0]['actual_old_paths_equal']==398;bindings.update(q['bindings']);bindings[str(quality)]=sha(quality)
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,success=success,stages=rows,workflow_seconds=elapsed,scope=manifest['scope']),indent=2)+'\n');print(dict(success=success,workflow_seconds=elapsed),flush=True)
if not success:raise SystemExit(1)
