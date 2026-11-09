"""Recompute all native bit-atom pin tuples from the complete gate JSON."""
import hashlib,json
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments'
B=E/'full_ram_native_slices_v1_2026-10-09'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
r=json.loads((B/'receipt.json').read_text())
for p,h in r['bindings'].items():assert sha(p)==h
source=E/'full_native_ram_gates_v3_2026-10-09/gates.json'
m=json.loads(source.read_text())['modules']['VexRiscvFull']
wire=lambda b:'b'+str(b) if type(b)is int else 'const'+b
expected=Counter()
for c in m['cells'].values():
    if c['type']!='dual_port_ram':continue
    conn=c['connections']
    for lane in range(20):
        pins=[]
        for pin,bits in conn.items():
            if pin in ('data1','data2','out1','out2'):pins.append(pin+'='+wire(bits[lane]))
            else:
                for i,b in enumerate(bits):pins.append((pin if len(bits)==1 else f'{pin}[{i}]')+'='+wire(b))
        expected[tuple(sorted(pins))]+=1
actual=Counter(tuple(sorted(line.split()[2:])) for line in (B/'design.blif').read_text().splitlines() if line.startswith('.subckt dual_port_ram '))
assert actual==expected and sum(actual.values())==300
def untouched(text):
    kept=[];rammodel=False
    for line in text.splitlines():
        if line=='.model dual_port_ram':rammodel=True
        if rammodel or line.startswith('.subckt dual_port_ram '):continue
        kept.append(line)
    return kept
original=E/'full_native_ram_blif_v1_2026-10-09/design.blif'
assert untouched(original.read_text())==untouched((B/'design.blif').read_text())
out=dict(passed=True,native_bit_atoms_exact=300,all_nonram_blif_content_exact=True,
    bindings={str(p):sha(p) for p in [Path(__file__),source,original,B/'design.blif',B/'receipt.json']},
    scope='Exact per-lane connection coverage and unchanged logic/top/FF/init BLIF. Not actual pack, arbitrary initial-state correspondence or Full equivalence.')
(B/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print('300 bit atoms independently verified')
