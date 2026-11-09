"""Frozen whole-family cold/live/live/cold lifecycle block."""
import json
import subprocess
import time
from pathlib import Path
from pre_route_endpoints import sha

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'experiments/live_loaded_cold_ABBA_2026-10-06';out.mkdir()
specs=[]
for index,mode in enumerate(('cold','live','live','cold')):
    old='cold_canonical_two_updates' if mode=='cold' else 'live_loaded_two_updates'
    name=f'live_loaded_cold_ABBA{index}_{mode}'
    files=[]
    for kind in ('trial','verify'):
        source=ROOT/'tools'/f'{kind}_{old}.py'
        dest=ROOT/'tools'/f'{kind}_{name}.py'
        dest.write_text(source.read_text().replace(old+'_2026-10-06',name+'_2026-10-06'))
        files.append(str(dest))
    specs.append(dict(index=index,mode=mode,experiment=name+'_2026-10-06',commands=[['python3',f] for f in files],sources={f:sha(f) for f in files}))
(out/'protocol.json').write_text(json.dumps(dict(runs=specs,source_sha256=sha(Path(__file__)),scope='Four whole-family fresh lifecycle runs, fixed cold/live/live/cold order, allcases/timings retained. Own policy canonical state evolution; identical original reload/direct audit/import scope. Single ABBA block not statistical confidence, from-design timing or hardware evidence.'),indent=2)+'\n')
rows=[]
for spec in specs:
    stages=[]
    for index,cmd in enumerate(spec['commands']):
        assert all(sha(f)==h for f,h in spec['sources'].items())
        log=out/f"run{spec['index']}_stage{index}.log";start=time.perf_counter()
        with log.open('w') as stream:code=subprocess.run(cmd,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,timeout=300).returncode
        stages.append(dict(command=cmd,exit_code=code,wall_s=time.perf_counter()-start,log_sha256=sha(log)))
        print(spec['index'],spec['mode'],index,code,flush=True)
        if code:break
    rows.append(dict(index=spec['index'],mode=spec['mode'],stages=stages))
    (out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n')
    if len(stages)!=2 or any(s['exit_code'] for s in stages):raise SystemExit('failed block retained')
