"""Independent forward cone inventory for undefined inputs up to sequential/top boundaries."""
import json,hashlib
from pathlib import Path
from collections import defaultdict,deque
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'briey_undefined_fanout_v1_2026-10-09';D.mkdir(exist_ok=False);p=E/'briey_lowered_synthesis_v1_2026-10-09/design.json';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();before=sha(p);m=json.loads(p.read_text())['modules']['Briey'];consumers=defaultdict(list);outputs=defaultdict(list)
for n,c in m['cells'].items():
 for port,bits in c['connections'].items():
  if c['port_directions'][port]=='input':
   for bit in bits:consumers[bit].append((n,port))
for name,port in m['ports'].items():
 if port['direction']=='output':
  for i,bit in enumerate(port['bits']):outputs[bit].append((name,i))
seeds=[(n,c) for n,c in m['cells'].items() if any(bit=='x' for bits in c['connections'].values() for bit in bits)];queue=deque(c['connections']['Y'][0] for n,c in seeds);seen=set(queue);logic=set(n for n,c in seeds);sinks=set();top=set()
while queue:
 bit=queue.popleft();top.update(outputs[bit])
 for n,port in consumers[bit]:
  c=m['cells'][n]
  if c['type'].startswith('$_DFF'):sinks.add((n,port,bit));continue
  assert c['type'] in ('$_MUX_','$_AND_','$_OR_','$_NOT_','$_XOR_');logic.add(n)
  q=c['connections']['Y'][0]
  if q not in seen:seen.add(q);queue.append(q)
assert sha(p)==before;selected={n:m['cells'][n] for n in sorted(logic)};gateoutputs={c['connections']['Y'][0] for c in selected.values()};inputs={bit for c in selected.values() for port,bits in c['connections'].items() if c['port_directions'][port]=='input' for bit in bits if type(bit)==int and bit not in gateoutputs}
report=dict(bindings={str(p):before,str(Path(__file__).resolve()):sha(__file__)},seed_cells=[n for n,c in seeds],forward_gate_count=len(logic),external_binary_bits=sorted(inputs),sequential_sinks=[dict(cell=n,port=port,bit=bit) for n,port,bit in sorted(sinks)],top_sinks=sorted(top),scope='Structural fanout only; no observability, reachability or legal constant replacement proof.')
(D/'cone.json').write_text(json.dumps(dict(cells=selected,external_bits=sorted(inputs)),indent=2)+'\n');report['bindings'][str(D/'cone.json')]=sha(D/'cone.json');(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('gates',len(logic),'externalbits',len(inputs),'FFsinks',len(sinks),'tops',len(top))
