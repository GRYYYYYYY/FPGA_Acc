"""Complete all-gate and native-boundary audit before ABC mapping."""
import hashlib,json
from pathlib import Path
from combinational_cut_native_ram_v1 import export_native
from audit_vexriscv_cut_export_v2 import audit
R=Path(__file__).resolve().parents[1]; E=R/'experiments'
D=E/'full_native_ram_cut_v1_2026-10-09'; D.mkdir(exist_ok=False)
source=E/'full_native_ram_gates_v3_2026-10-09/gates.json'
proof=E/'full_native_ram_gate_controls_v1_2026-10-09/verification.json'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=json.loads(proof.read_text());assert p['passed']
for path,h in p['bindings'].items():assert sha(path)==h
m=json.loads(source.read_text())['modules']['VexRiscvFull']
text,records,cut,boundary=export_native(m)
result=audit(cut,text,boundary)
# Independently derive boundary union directly from original top/FF/RAM directions.
ins=set(); outs=set()
for port in m['ports'].values():(ins if port['direction']=='input' else outs).update(port['bits'])
for cell in m['cells'].values():
    if not (cell['type'].startswith('$_DFF') or cell['type']=='dual_port_ram'):continue
    for pin,bits in cell['connections'].items():
        (ins if cell['port_directions'][pin]=='output' else outs).update(bits)
token=lambda b:'b'+str(b) if type(b) is int else 'const'+b
blif_inputs=next(line.split()[1:] for line in text.splitlines() if line.startswith('.inputs '))
blif_outputs=next(line.split()[1:] for line in text.splitlines() if line.startswith('.outputs '))
assert set(blif_inputs)=={token(b) for b in ins if type(b) is int}
assert set(blif_outputs)=={token(b) for b in outs}
assert records['ports']==m['ports'] and len(records['native_ram'])==15
assert records['initialized_nets']=={n:v for n,v in m['netnames'].items() if 'init' in v['attributes']}
(D/'original.blif').write_text(text)
(D/'reconstruction.json').write_text(json.dumps(records,indent=2)+'\n')
bindings={str(path):sha(path) for path in [Path(__file__),source,proof,R/'tools/combinational_cut_native_ram_v1.py',R/'tools/combinational_cut_export_v3.py',R/'tools/audit_vexriscv_cut_export_v2.py',D/'original.blif',D/'reconstruction.json']}
(D/'verification.json').write_text(json.dumps(dict(passed=True,bindings=bindings,result=result,
    native_ram_instances=15,scope='All original gates truth tables and union of original top/FF/RAM pins audited. Native RAM functional semantics, mapped CEC and Full sequential equivalence not proven.'),indent=2)+'\n')
print(result)
