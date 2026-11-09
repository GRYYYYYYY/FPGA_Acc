"""Rebuild all mapped logic, FF initialization, original ports and native RAM pins."""
import hashlib,json,subprocess
from pathlib import Path
from sequential_blif_contract_v1 import emit
R=Path(__file__).resolve().parents[1]; E=R/'experiments'
D=E/'full_native_ram_blif_v1_2026-10-09'; D.mkdir(exist_ok=False)
B=E/'full_native_ram_cut_mapping_v1_2026-10-09'
proof=B/'receipt.json'; r=json.loads(proof.read_text()); assert r['cut_equivalence_pass']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for p,h in {**r['bindings'],**r['files']}.items():assert sha(Path(p))==h
source=E/'full_native_ram_gates_v3_2026-10-09/gates.json'
m=json.loads(source.read_text())['modules']['VexRiscvFull']
records=json.loads((E/'full_native_ram_cut_v1_2026-10-09/reconstruction.json').read_text())
assert records['ports']==m['ports']
wire=lambda b:'b'+str(b) if type(b) is int else 'const'+b
inputs=[];outputs=[];aliases=[]
for name,p in m['ports'].items():
    for i,bit in enumerate(p['bits']):
        label=name if len(p['bits'])==1 else f'{name}[{i}]'
        (inputs if p['direction']=='input' else outputs).append(label)
        src,dst=(label,wire(bit)) if p['direction']=='input' else (wire(bit),label)
        aliases.extend(['.names '+src+' '+dst,'1 1'])
lines=['.model VexRiscvFull','.inputs '+' '.join(inputs),'.outputs '+' '.join(outputs)]+aliases
pending=''
for raw in (B/'mapped.blif').read_text().splitlines():
    pending+=raw.strip()
    if pending.endswith(chr(92)):pending=pending[:-1]+' ';continue
    line=pending;pending=''
    if line.startswith(('.model ','.inputs ','.outputs ')) or line=='.end':continue
    lines.append(line)
assert not pending
seq,seqrecords=emit(m);lines+=seq
ramrecords=[]
for name,c in records['native_ram'].items():
    assert c==m['cells'][name]
    pins=[]
    for pin,bits in c['connections'].items():
        for i,bit in enumerate(bits):
            label=pin if len(bits)==1 else f'{pin}[{i}]'
            pins.append(label+'='+wire(bit))
    lines.append('.subckt dual_port_ram '+' '.join(pins))
    ramrecords.append(dict(cell=name,pins=pins))
lines.append('.end')
for kind in ['$_DFF_PP0_','$_DFF_PP1_']:
    lines+=['.model '+kind,'.inputs C D R','.outputs Q','.blackbox','.end']
ram=next(iter(records['native_ram'].values()))
modelinputs=[];modeloutputs=[]
for pin,bits in ram['connections'].items():
    target=modelinputs if ram['port_directions'][pin]=='input' else modeloutputs
    target.extend(pin if len(bits)==1 else f'{pin}[{i}]' for i in range(len(bits)))
lines+=['.model dual_port_ram','.inputs '+' '.join(modelinputs),'.outputs '+' '.join(modeloutputs),'.blackbox','.end']
(D/'design.blif').write_text('\n'.join(lines)+'\n')
(D/'reconstruction_records.json').write_text(json.dumps(dict(sequential=seqrecords,native_ram=ramrecords),indent=2)+'\n')
yr=json.loads((E/'vexriscv_family_flattened_inventory_v1_2026-10-09/protocol.json').read_text())
y=Path(next(p for p in yr['bindings'] if p.endswith('/bin/yosys')));assert sha(y)==yr['bindings'][str(y)]
(D/'reload.ys').write_text('read_blif design.blif\nhierarchy -check -top VexRiscvFull\ncheck -assert\nwrite_json reload.json\n')
bindings={str(p):sha(p) for p in [Path(__file__),proof,source,B/'mapped.blif',R/'tools/sequential_blif_contract_v1.py',y,D/'design.blif',D/'reconstruction_records.json',D/'reload.ys']}
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,timeout_s=120,scope='Full RAM/FF/init structural reconstruction and fresh BLIF reload; no native packing, Full functional equivalence or timing claim.'),indent=2)+'\n')
with (D/'reload.log').open('x') as log:
    try:code=subprocess.run([str(y),'-s','reload.ys'],cwd=D,stdout=log,stderr=subprocess.STDOUT,timeout=120).returncode
    except subprocess.TimeoutExpired:code='TIMEOUT'
out=dict(bindings=bindings,exit_code=code,sequential_cells=len(seqrecords),initialized_latches=sum(r['init']!='2' for r in seqrecords),native_ram_instances=len(ramrecords),admitted_for_prediction=False,files={str(p):sha(p) for p in D.iterdir() if p.is_file()})
(D/'receipt.json').write_text(json.dumps(out,indent=2)+'\n');print(code,out['initialized_latches'],len(ramrecords))
