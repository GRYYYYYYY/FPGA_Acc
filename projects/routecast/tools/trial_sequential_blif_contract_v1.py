import json,hashlib
from pathlib import Path
from collections import Counter
from sequential_blif_contract_v1 import emit
R=Path(__file__).resolve().parents[1];B=R/'experiments/vexriscv_family_flattened_inventory_v1_2026-10-09';D=R/'experiments/vexriscv_sequential_blif_contract_v1_2026-10-09';D.mkdir(exist_ok=False)
p=B/'Briey/design.json';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();before=sha(p);m=json.loads(p.read_text())['modules']['Briey'];lines,records=emit(m);assert sha(p)==before
# Independent expected plain FF table from original JSON, including explicit reverse bit order.
initial={b:v for n in m['netnames'].values() if 'init' in n.get('attributes',{}) for b,v in zip(n['bits'],n['attributes']['init'][::-1]) if v!='x'}
expected=Counter()
for c in m['cells'].values():
 if c['type'] in ('$_DFF_P_','$_DFF_N_'):
  w=c['connections'];expected[(str(w['D'][0]),str(w['Q'][0]),'re' if c['type']=='$_DFF_P_' else 'fe',str(w['C'][0]),initial.get(w['Q'][0],'2'))]+=1
actual=Counter(tuple(t[1:] if t.startswith('b') else t for t in line.split()[1:]) for line in lines if line.startswith('.latch '));assert actual==expected
(D/'sequential.blif.fragment').write_text('\n'.join(lines)+'\n');report=dict(bindings={str(x):sha(x) for x in (p,Path(__file__).resolve(),R/'tools/sequential_blif_contract_v1.py',D/'sequential.blif.fragment')},cells=dict(Counter(x['type'] for x in records)),initialized_plain_ff=sum(x['init']!='2' for x in records),negative_edge_ff=sum(x['type']=='$_DFF_N_' for x in records),scope='Sequential fragment and ordinary FF exact table check only. No complete circuit, async behavioral models, native timing or HDL sequential proof.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k!='bindings'})
