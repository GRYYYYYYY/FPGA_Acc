"""Fresh structural Yosys reload of reconstructed Full input, not functional proof."""
import json,hashlib,subprocess,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'vexriscv_full_mapped_structure_v1_2026-10-09';D=E/'vexriscv_full_blif_reload_v1_2026-10-09';D.mkdir(exist_ok=False);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();receipt=json.loads((B/'receipt.json').read_text())
for p,h in receipt['bindings'].items():assert sha(p)==h
plan=json.loads((E/'vexriscv_family_flattened_inventory_v1_2026-10-09/protocol.json').read_text());yosys=Path(next(p for p in plan['bindings'] if p.endswith('/bin/yosys')));assert sha(yosys)==plan['bindings'][str(yosys)];shutil.copyfile(B/'design.blif',D/'design.blif');(D/'reload.ys').write_text('read_blif design.blif\nhierarchy -check -top VexRiscvFull\ncheck -assert\nwrite_json reload.json\n');bindings={str(p):sha(p) for p in (Path(__file__).resolve(),B/'receipt.json',B/'design.blif',yosys,D/'design.blif',D/'reload.ys')};command=[str(yosys),'-s','reload.ys'];(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,command=command,timeout_s=120),indent=2)+'\n')
with (D/'log.txt').open('x') as log:
 try:code=subprocess.run(command,cwd=D,stdout=log,stderr=subprocess.STDOUT,timeout=120).returncode
 except subprocess.TimeoutExpired:code='TIMEOUT'
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,exit_code=code,files={str(p):sha(p) for p in D.iterdir() if p.is_file()},scope='Parse/check/readback only, no whole HDL sequential equivalence, native pack or prediction admission.'),indent=2)+'\n');print('exit',code)
