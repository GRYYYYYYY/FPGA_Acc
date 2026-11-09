"""Three GF2 native same-process repeated-import probes."""
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from pre_route_endpoints import sha

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'experiments/native_repeat_import_gf2_2026-10-06';out.mkdir()
build=ROOT/'build/native_repeat_import_probe_2026-10-06';binary=build/'repeat_import_vpr'
assert sha(binary)==json.loads((build/'receipt.json').read_text())['binary_sha256']
shared=ROOT.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07'
arch=shared/'vtr_flow/arch/timing/k6_frac_N10_40nm.xml'
specs=[]
for width in (32,64,128):
    source=ROOT/f'work/gf2_recurrence_native_reference_2026-10-06/gf2_d{width}'
    specs.append(dict(width=width,source=str(source),inputs={str(source/n):sha(source/n) for n in ('design.blif','design.net','design.place','design.route','rr_graph.xml')}))
(out/'protocol.json').write_text(json.dumps(dict(cases=specs,binary_sha256=sha(binary),architecture_sha256=sha(arch),source_sha256=sha(Path(__file__)),scope='Same-placement same-NET duplicate import then native routing. Not cross-placement estimator import, fresh STA parity, rollback or cost evidence.'),indent=2)+'\n')
results=[]
for spec in specs:
    work=out/f"gf2_d{spec['width']}";work.mkdir();source=Path(spec['source'])
    for n in ('design.blif','design.net','design.place'):shutil.copyfile(source/n,work/n)
    shutil.copyfile(source/'design.route',work/'seed.route')
    cmd=[str(binary),str(arch),'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','output.route','--read_rr_graph',str(source/'rr_graph.xml'),'--route_chan_width','128','--num_workers','1','--check_route','full','--max_router_iterations','100']
    env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
    env.update(ROUTECAST_NATIVE_SEED=str(work/'seed.route'),ROUTECAST_REPEAT_IMPORT='1')
    log=work/'run.log'
    with log.open('w') as stream:code=subprocess.run(cmd,cwd=work,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=180).returncode
    text=log.read_text();match=re.search(r'repeated import FULL sink-delay and occupancy parity passed sinks=(\d+) nodes=(\d+)',text)
    results.append(dict(width=spec['width'],exit_code=code,parity_marker=bool(match),sinks=int(match[1]) if match else None,nodes=int(match[2]) if match else None,log_sha256=sha(log),command=cmd))
    assert all(sha(path)==h for path,h in spec['inputs'].items())
    (out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=results),indent=2)+'\n')
    print(spec['width'],code,bool(match),flush=True)
