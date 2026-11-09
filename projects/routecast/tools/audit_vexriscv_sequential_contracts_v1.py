"""Authenticate completed flattened snapshots; enumerate clock polarity and initialization obligations."""
import json,hashlib
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];B=R/'experiments/vexriscv_family_flattened_inventory_v1_2026-10-09';D=R/'experiments/vexriscv_sequential_contracts_v1_2026-10-09'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
protocol=json.loads((B/'protocol.json').read_text())
for p,h in protocol['bindings'].items():assert sha(p)==h
progressbytes=(B/'progress.json').read_bytes();completed=json.loads(progressbytes);records=[];bindings={str(Path(__file__).resolve()):sha(__file__),str(B/'protocol.json'):sha(B/'protocol.json')}
for row in completed:
 if row['exit_code']!=0:records.append(dict(member=row['member'],status='FAILED',exit_code=row['exit_code']));continue
 p=B/row['member']/'design.json';digest=sha(p);modules=json.loads(p.read_text())['modules'];assert len(modules)==1;module=modules[row['top']];cells=module['cells'];types=Counter(c['type'] for c in cells.values());assert dict(types)==row['hierarchical_cell_types'];drivers={};negative=[]
 for name,c in cells.items():
  if not c['type'].startswith('$_DFF'):continue
  assert set(c['connections'])==({'C','D','Q','R'} if len(c['type'])>8 else {'C','D','Q'}),(name,c['type'])
  for bits in c['connections'].values():assert len(bits)==1
  q=c['connections']['Q'][0];assert q not in drivers;drivers[q]=(name,c)
  if c['type']=='$_DFF_N_':negative.append(dict(cell=name,ports=c['connections'],source=c['attributes'].get('src')))
 initbits={};initnames=[]
 for name,net in module['netnames'].items():
  value=net.get('attributes',{}).get('init')
  if value is None:continue
  assert len(value)==len(net['bits']);initnames.append(name)
  for bit,v in zip(net['bits'],reversed(value)):
   if v=='x':continue
   assert v in ('0','1') and type(bit)==int
   if bit in initbits:assert initbits[bit]==v
   initbits[bit]=v
 initialized=[]
 for bit,v in sorted(initbits.items()):
  assert bit in drivers,(row['member'],bit,'initialized wire not driven by FF')
  name,c=drivers[bit];initialized.append(dict(q_bit=bit,initial_value=v,cell=name,type=c['type'],ports=c['connections']))
 assert sha(p)==digest;bindings[str(p)]=digest;records.append(dict(member=row['member'],status='CONTRACT_INVENTORIED',negative_edge_flops=negative,initialized_bits=initialized,init_net_names=initnames,ff_types={k:v for k,v in types.items() if k.startswith('$_DFF')}))
D.mkdir(exist_ok=False);(D/'progress_snapshot.json').write_bytes(progressbytes);bindings[str(D/'progress_snapshot.json')]=sha(D/'progress_snapshot.json');report=dict(bindings=bindings,completed_members=len(completed),records=records,scope='Completed snapshot only. Initialization bit order, unique aliases and FF Q correspondence; negative edge obligations. No full-family completion, HDL equivalence or native architecture support proof.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print([(x['member'],len(x.get('negative_edge_flops',[])),len(x.get('initialized_bits',[]))) for x in records])
