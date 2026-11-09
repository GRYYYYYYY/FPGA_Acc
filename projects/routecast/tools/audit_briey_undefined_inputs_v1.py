"""Inventory undefined bits without substituting deterministic values."""
import json,hashlib
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'briey_undefined_inputs_v1_2026-10-09';D.mkdir(exist_ok=False);p=E/'briey_lowered_synthesis_v1_2026-10-09/design.json';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();before=sha(p);m=json.loads(p.read_text())['modules']['Briey'];bytype=Counter();byvalue=Counter();examples=[];allcells=set()
for name,c in m['cells'].items():
 for port,bits in c['connections'].items():
  for index,bit in enumerate(bits):
   if type(bit)==int or bit in ('0','1'):continue
   bytype[c['type']]+=1;byvalue[str(bit)]+=1;allcells.add(name)
   if len(examples)<30:examples.append(dict(cell=name,type=c['type'],port=port,index=index,value=bit,direction=c['port_directions'][port],source=c['attributes'].get('src')))
assert sha(p)==before;report=dict(bindings={str(p):before,str(Path(__file__).resolve()):sha(__file__)},undefined_pin_counts=dict(byvalue),cell_type_pin_counts=dict(bytype),cells_with_undefined=len(allcells),examples=examples,scope='Undefined X/Z pin census only; failed cut not admitted. No constant substitution, nondeterministic abstraction, HDL equivalence or prediction readiness claim.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k not in ('bindings','examples')})
