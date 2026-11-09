"""Lower wide RAM BLIF instances to VPR memory-class one-data-bit atoms."""
import hashlib,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1]; E=R/'experiments'
D=E/'full_ram_native_slices_v1_2026-10-09';D.mkdir(exist_ok=False)
B=E/'full_native_ram_blif_v1_2026-10-09'
proof=E/'full_native_ram_blif_verification_v1_2026-10-09/verification.json'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
r=json.loads(proof.read_text());assert r['passed']
for p,h in r['bindings'].items():assert sha(p)==h
source=B/'design.blif'
archsource=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/libs/libarchfpga/src/arch_util.cpp'
assert 'void ProcessMemoryClass' in archsource.read_text()
lines=[];records=[];in_ram_model=False
for line in source.read_text().splitlines():
    if line=='.model dual_port_ram':in_ram_model=True
    if line.startswith('.subckt dual_port_ram '):
        pins=dict(word.split('=') for word in line.split()[2:])
        for lane in range(20):
            out={}
            for pin,value in pins.items():
                match=re.fullmatch(r'(data[12]|out[12])\[(\d+)\]',pin)
                if match:
                    if int(match[2])==lane:out[match[1]]=value
                else:out[pin]=value
            assert len(out)==27
            lines.append('.subckt dual_port_ram '+' '.join(k+'='+v for k,v in sorted(out.items())))
            records.append(dict(wide_instance=len(records)//20,lane=lane,pins=out))
    elif in_ram_model and line.startswith(('.inputs ','.outputs ')):
        direction=line.split()[0]; tokens=[]
        for pin in line.split()[1:]:
            match=re.fullmatch(r'(data[12]|out[12])\[(\d+)\]',pin)
            if match:
                if int(match[2])==0:tokens.append(match[1])
            else:tokens.append(pin)
        lines.append(direction+' '+' '.join(tokens))
    else:lines.append(line)
assert len(records)==300
(D/'design.blif').write_text('\n'.join(lines)+'\n')
(D/'slice_records.json').write_text(json.dumps(records,indent=2)+'\n')
bindings={str(p):sha(p) for p in [Path(__file__),proof,source,archsource,D/'design.blif',D/'slice_records.json']}
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,native_atoms=300,wide_candidates=15,
    scope='VPR ProcessMemoryClass forces data ports to one bit and broadcasts controls/addresses. Each wide memory is lowered to 20 bit atoms; physical packing count not yet established.',admitted_for_prediction=False),indent=2)+'\n')
print('300 native one-bit atoms emitted')
