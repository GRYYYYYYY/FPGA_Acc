"""Fresh GF2 estimator imports with prescribed accept/reject frame probes."""
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from pre_route_endpoints import placements, sha

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'experiments/native_loaded_candidate_import_gf2_2026-10-06';out.mkdir()
build=ROOT/'build/native_loaded_candidate_import_v2_2026-10-06';binary=build/'import_vpr'
assert sha(binary)==json.loads((build/'receipt.json').read_text())['binary_sha256']
shared=ROOT.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07'
arch=shared/'vtr_flow/arch/timing/k6_frac_N10_40nm.xml'
specs=[]
for width in (32,64,128):
    original=ROOT/f'work/gf2_recurrence_native_reference_2026-10-06/gf2_d{width}'
    candidate=ROOT/f'work/gf2_identity_reuse_continuous_two_updates_v2_2026-10-06/gf2_d{width}/0/work/gf2_d{width}_native_seeded_native_import_2026-10-06'
    assert sha(original/'design.net')==sha(candidate/'design.net')
    old=placements(original/'design.place',sha(original/'design.net'))
    new=placements(candidate/'design.place',sha(candidate/'design.net'))
    moved=[n for n in old if old[n]!=new[n]];assert len(moved)==2
    a,b=moved;assert old[a][:4]==new[b][:4] and old[b][:4]==new[a][:4]
    inputs=[*(original/n for n in ('design.blif','design.net','design.place','design.route','rr_graph.xml')),
            *(candidate/n for n in ('design.place','design.route'))]
    specs.append(dict(width=width,original=str(original),candidate=str(candidate),pairs=f'{old[a][4]} {old[b][4]}',inputs={str(p):sha(p) for p in inputs}))
(out/'protocol.json').write_text(json.dumps(dict(cases=specs,decisions=['A','R'],binary_sha256=sha(binary),architecture_sha256=sha(arch),source_sha256=sha(Path(__file__)),scope='Single-step estimator import at swapped placement; prescribed accept/reject, not cold-reference quality gate or whole lifecycle timing.'),indent=2)+'\n')
rows=[]
for spec in specs:
    for decision in ('A','R'):
        work=out/f"gf2_d{spec['width']}_{decision}";work.mkdir()
        original=Path(spec['original']);candidate=Path(spec['candidate'])
        for name in ('design.blif','design.net','design.place'):shutil.copyfile(original/name,work/name)
        shutil.copyfile(original/'design.route',work/'seed.route');shutil.copyfile(candidate/'design.route',work/'predicted.route')
        cmd=[str(binary),str(arch),'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','output.route','--read_rr_graph',str(original/'rr_graph.xml'),'--route_chan_width','128','--num_workers','1','--check_route','full','--max_router_iterations','100']
        env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
        env.update(ROUTECAST_NATIVE_SEED=str(work/'seed.route'),ROUTECAST_IMPORTED_CANDIDATE=str(work/'predicted.route'),ROUTECAST_TIMING_RESTORE_PROBE='1',ROUTECAST_MOVE_SEQUENCE=decision,ROUTECAST_MOVE_PAIRS=spec['pairs'])
        log=work/'run.log'
        with log.open('w') as stream:code=subprocess.run(cmd,cwd=work,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=180).returncode
        text=log.read_text();cpd=re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)
        rows.append(dict(width=spec['width'],decision=decision,exit_code=code,command=cmd,log_sha256=sha(log),import_marker='imported external candidate in loaded context' in text,restored_marker='restored delay matrix and all edge-delay/STA metric observations' in text,cpd_ns=float(cpd[1]) if cpd else None,files={str(p):sha(p) for p in work.iterdir() if p.is_file()}))
        assert all(sha(p)==h for p,h in spec['inputs'].items())
        (out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n')
        print(spec['width'],decision,code,rows[-1]['import_marker'],rows[-1]['restored_marker'],flush=True)
