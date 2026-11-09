"""Independent packed-XML architecture mode traversal and sequential model census."""
import json,re,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'full_native_ram_pack_v2_2026-10-09';D=E/'full_native_ram_packed_models_v1_2026-10-09'
receipt=json.loads((B/'receipt.json').read_text());assert receipt['exit_code']==0 and receipt['pack_net_exists']
for p,h in {**receipt['bindings'],**receipt['files']}.items():assert sha(p)==h
plan=json.loads((B/'protocol.json').read_text());arch=Path(plan['command'][1]);x=ET.parse(arch).getroot();top={p.get('name'):p for p in x.find('complexblocklist')};packed=ET.parse(B/'design.net').getroot();counts=Counter();records=[];physical_memories=[]
def visit(block,pb):
 if block.get('name')=='open':return
 kind=re.sub(r'\[\d+\]$','',block.get('instance'));assert kind==pb.get('name'),(kind,pb.get('name'))
 model=pb.get('blif_model')
 if model and pb.get('class')=='memory':
  children=[c for c in block.findall('block') if c.get('name')!='open']
  assert block.get('mode') in ('memory_slice','memory_slice_1bit')
  data_ports=[p for p in pb if p.tag in ('input','output') and (p.get('port_class') or '').startswith('data')]
  assert data_ports and len({int(p.get('num_pins')) for p in data_ports})==1
  capacity=int(data_ports[0].get('num_pins'))
  assert 0<len(children)<=capacity
  physical_memories.append(dict(name=block.get('name'),mode=pb.get('name'),occupied_bit_slices=len(children),capacity_bit_slices=capacity))
  for leaf in children:
   assert re.sub(r'\[\d+\]$','',leaf.get('instance')) in ('memory_slice','memory_slice_1bit')
   assert not leaf.findall('block')
   counts[model]+=1
  return
 if model:
  children=block.findall('block')
  if children:
   assert model=='.names' and pb.get('class')=='lut' and block.get('mode')==pb.get('name')
   occupied=[c for c in children if c.get('name')!='open'];assert len(occupied)==1
   leaf=occupied[0];assert leaf.get('instance')=='lut[0]' and leaf.get('name')==block.get('name') and not leaf.findall('block')
  counts[model]+=1
  if 'DFF_PP' in model:records.append(dict(name=block.get('name'),model=model,instance=block.get('instance')))
  return
 scope=pb
 if block.get('mode') is not None:
  modes=pb.findall('mode')
  if modes:
   choices=[mode for mode in modes if mode.get('name')==block.get('mode')];assert len(choices)==1;scope=choices[0]
  else:
   assert block.get('mode')=='default';assert pb.findall('pb_type')
 children={child.get('name'):child for child in scope.findall('pb_type')}
 for child in block.findall('block'):
  if child.get('name')=='open':continue
  name=re.sub(r'\[\d+\]$','',child.get('instance'));assert name in children;visit(child,children[name])
for block in packed.findall('block'):
 if block.get('name')=='open':continue
 name=re.sub(r'\[\d+\]$','',block.get('instance'));assert name in top;visit(block,top[name])
assert counts['.subckt dual_port_ram']==174
assert counts['.latch']==2100 and counts['.subckt $_DFF_PP0_']==109 and counts['.subckt $_DFF_PP1_']==6
bindings={str(p):sha(p) for p in (Path(__file__).resolve(),B/'receipt.json',B/'protocol.json',B/'design.net',arch)}
D.mkdir(exist_ok=False);(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,models=dict(counts),reset_records=records,physical_memories=physical_memories,scope='Packed architecture-selected primitive model census, all ordinary/reset FF counts preserved. No reset-pin connectivity tracing, sequential functional proof, placement/routing label or characterized timing claim.'),indent=2)+'\n');print(dict(models=dict(counts),reset_records=len(records),physical_ram_groups=len(physical_memories)),flush=True)
