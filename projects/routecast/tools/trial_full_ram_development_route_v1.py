"""Engineering placement of the complete RAM candidate with explicit frozen SDC."""
import hashlib,json,os,shutil,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments'
D=E/'full_ram_development_route_v1_2026-10-09';D.mkdir(exist_ok=False)
B=E/'full_native_ram_pack_v2_2026-10-09'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
proofs=[B/'receipt.json',E/'full_native_ram_packed_pins_v1_2026-10-09/verification.json',
    E/'full_native_ram_packed_reset_pins_v1_2026-10-09/verification.json',
    E/'full_native_ram_packed_ordinary_pins_v2_2026-10-09/verification.json',
    E/'vexriscv_full_development_sdc_v1_2026-10-09/protocol.json']
for proof in proofs:
    p=json.loads(proof.read_text())
    for path,h in p['bindings'].items():assert sha(path)==h
place=E/'full_ram_development_place_v1_2026-10-09'
proofs.append(place/'verification.json')
assert json.loads((place/'verification.json').read_text())['passed']
pack=json.loads((B/'receipt.json').read_text());assert pack['exit_code']==0 and pack['pack_net_exists']
for path,h in pack['files'].items():assert sha(path)==h
protocol=json.loads((B/'protocol.json').read_text());vpr=Path(protocol['command'][0]);arch=Path(protocol['command'][1])
sdc=E/'vexriscv_full_development_sdc_v1_2026-10-09/development.sdc'
for src,dst in [(B/'design.blif',D/'design.blif'),(B/'design.net',D/'design.net'),(sdc,D/'development.sdc'),(place/'design.place',D/'design.place')]:shutil.copyfile(src,dst)
command=[str(vpr),str(arch),'design.blif','--route','--net_file','design.net','--place_file','design.place',
    '--sdc_file','development.sdc','--route_chan_width','128','--num_workers','1','--seed','1','--write_rr_graph','rr_graph.xml']
bindings={str(p):sha(p) for p in [Path(__file__),*proofs,vpr,arch,sdc,D/'design.blif',D/'design.net',D/'development.sdc',D/'design.place']}
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,command=command,timeout_s=600,
    scope='Complete Full native RAM candidate engineering fixed-placement routing only, explicit predeclared 20ns clock and 2ns max IO. Reuses independently audited packed input and placement without repack/replacement. Reset timing placeholders, Full sequential equivalence and physical initialization unresolved. Not independent product timing requirement, unseen-family admission or net-benefit evidence.'),indent=2)+'\n')
t=time.perf_counter()
with (D/'route.log').open('x') as log:
    try:code=subprocess.run(command,cwd=D,env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')},stdout=log,stderr=subprocess.STDOUT,timeout=600).returncode
    except subprocess.TimeoutExpired:code='TIMEOUT'
assert all(sha(p)==h for p,h in bindings.items())
out=dict(bindings=bindings,exit_code=code,seconds=time.perf_counter()-t,route_exists=(D/'design.route').exists(),
    admitted_for_prediction=False,files={str(p):sha(p) for p in D.iterdir() if p.is_file()})
(D/'receipt.json').write_text(json.dumps(out,indent=2)+'\n');print(code,out['route_exists'],out['seconds'],flush=True)
