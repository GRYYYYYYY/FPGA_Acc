"""Capture flattened process-level tri-state boundaries before gate synthesis."""
import json,subprocess,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'briey_bidir_boundary_v1_2026-10-09';D.mkdir(exist_ok=False)
b=E/'vexriscv_family_flattened_inventory_v1_2026-10-09';plan=json.loads((b/'protocol.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for p,h in plan['bindings'].items():assert sha(p)==h
source=b/'Briey/design.v';yosys=Path(next(p for p in plan['bindings'] if p.endswith('/bin/yosys')));(D/'design.v').write_bytes(source.read_bytes());(D/'prepare.ys').write_text('read_verilog design.v\nhierarchy -check -top Briey\nproc\nflatten\nwrite_json design.json\n')
command=[str(yosys),'-s','prepare.ys'];bindings={str(p):sha(p) for p in (source,yosys,Path(__file__).resolve(),D/'design.v',D/'prepare.ys')};(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,command=command,timeout_s=120,scope='Before gate synth tri-state capture only; no route labels or circuit admission.'),indent=2)+'\n')
with (D/'log.txt').open('x') as log:
 try:code=subprocess.run(command,cwd=D,stdout=log,stderr=subprocess.STDOUT,timeout=120).returncode
 except subprocess.TimeoutExpired:code='TIMEOUT'
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,exit_code=code,files={str(p):sha(p) for p in D.iterdir() if p.is_file()}),indent=2)+'\n');print('exit',code)
