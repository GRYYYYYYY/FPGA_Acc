"""Original standalone cold reference with identical second-gate NET/place."""
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from pre_route_endpoints import sha

ROOT=Path(__file__).resolve().parents[1]
parent=ROOT/'experiments/loaded_quality_gate_reverse_2026-10-06'
pr=json.loads((parent/'receipt.json').read_text());assert json.loads((parent/'verification.json').read_text())['receipt_sha256']==sha(parent/'receipt.json')
out=ROOT/'experiments/reverse_same_net_cold_reference_2026-10-06';out.mkdir()
binary=ROOT.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_vpr/vpr/vpr'
assert sha(binary)=='a90dc1b3380ebda705e85f176db0cc3d6be1b71ab9ee887db819febc8b62bafc'
specs=[]
for row in pr['rows']:
    work=out/f"gf2_d{row['width']}";work.mkdir();source=parent/f"gf2_d{row['width']}_A/identity_probe"
    for name in ('design.blif','design.net','design.place'):shutil.copyfile(source/name,work/name)
    cmd=row['command'].copy();cmd[0]=str(binary)
    specs.append(dict(width=row['width'],command=cmd,work=str(work),source=str(source),inputs={str(source/n):sha(source/n) for n in ('design.blif','design.net','design.place')}))
(out/'protocol.json').write_text(json.dumps(dict(parent_receipt_sha256=sha(parent/'receipt.json'),source_sha256=sha(Path(__file__)),binary_sha256=sha(binary),cases=specs,scope='Fresh standalone original cold routes with identical canonical NET/target placement; not lifecycle benefit benchmark. Native process walls exclude copies/protocol and audits.'),indent=2)+'\n')
env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};rows=[]
for spec in specs:
    work=Path(spec['work']);start=time.perf_counter()
    with (work/'run.log').open('w') as stream:code=subprocess.run(spec['command'],cwd=work,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=180).returncode
    elapsed=time.perf_counter()-start;log=(work/'run.log').read_text();cpd=re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)
    assert all(sha(p)==h for p,h in spec['inputs'].items())
    rows.append(dict(width=spec['width'],exit_code=code,cpd_ns=float(cpd[1]) if cpd else None,native_wall_s=elapsed,files={str(p):sha(p) for p in work.iterdir() if p.is_file()}))
    (out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n');print(spec['width'],code,rows[-1]['cpd_ns'],flush=True)
