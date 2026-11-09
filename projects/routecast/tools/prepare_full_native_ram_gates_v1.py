"""Fine gate lowering of complete Full candidate, preserving native RAM blackboxes."""
import hashlib
import json
import subprocess
import time
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1]; E=R/'experiments'
D=E/'full_native_ram_gates_v1_2026-10-09'; D.mkdir(exist_ok=False)
B=E/'full_ram_mapping_candidate_v1_2026-10-09'
proof=B/'independent_verification_v3.json'
p=json.loads(proof.read_text()); assert p['passed']
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
for path,h in p['bindings'].items():assert sha(Path(path))==h
receipt=json.loads((B/'receipt.json').read_text())
y=Path(next(path for path in receipt['bindings'] if path.endswith('/bin/yosys')))
assert sha(y)==receipt['bindings'][str(y)]
source=B/'structural.json'; (D/'input.json').write_bytes(source.read_bytes())
script='read_json input.json\nhierarchy -check -top VexRiscvFull\nsynth -top VexRiscvFull -noabc -run fine:\ndffunmap\ncheck -assert\nwrite_json gates.json\n'
(D/'prepare.ys').write_text(script)
bindings={str(path):sha(path) for path in [Path(__file__),proof,source,y,D/'input.json',D/'prepare.ys']}
command=[str(y),'-s','prepare.ys']
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,command=command,timeout_s=180,
    scope='Complete Full fine gate lowering with 15 native RAM blackboxes; no ABC/reset/init relaxation. Structural candidate only, not Full functional proof, native packing or prediction admission.'),indent=2)+'\n')
t=time.perf_counter()
with (D/'prepare.log').open('x') as log:
    try:code=subprocess.run(command,cwd=D,stdout=log,stderr=subprocess.STDOUT,timeout=180).returncode
    except subprocess.TimeoutExpired:code='TIMEOUT'
out=dict(bindings=bindings,exit_code=code,seconds=time.perf_counter()-t,admitted_for_prediction=False)
if code==0:
    modules=json.loads((D/'gates.json').read_text())['modules']; m=modules['VexRiscvFull']
    types=Counter(c['type'] for c in m['cells'].values())
    assert types['dual_port_ram']==15 and not any(k.startswith('$mem') for k in types)
    original=json.loads(source.read_text())['modules']['VexRiscvFull']
    assert m['ports']==original['ports']
    out.update(cell_types=dict(types),top_ports_exact=True,
        init_nets={n:v['attributes']['init'] for n,v in m['netnames'].items() if 'init' in v['attributes']})
out['files']={str(path):sha(path) for path in D.iterdir() if path.is_file()}
(D/'receipt.json').write_text(json.dumps(out,indent=2)+'\n')
print(code,out.get('cell_types'),flush=True)
