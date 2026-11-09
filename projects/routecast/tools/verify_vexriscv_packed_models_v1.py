"""Independent packed-XML architecture mode traversal and sequential model census."""
import json,re,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'vexriscv_native_pack_v1_2026-10-09';D=E/'vexriscv_packed_models_v1_2026-10-09'
receipt=json.loads((B/'receipt.json').read_text());assert receipt['exit_code']==0 and receipt['pack_net_exists']
for p,h in {**receipt['bindings'],**receipt['files']}.items():assert sha(p)==h
plan=json.loads((B/'protocol.json').read_text());arch=Path(plan['command'][1]);x=ET.parse(arch).getroot();top={p.get('name'):p for p in x.find('complexblocklist')};packed=ET.parse(B/'design.net').getroot();counts=Counter();records=[]
def visit(block,pb):
 if block.get('name')=='open':return
 kind=re.sub(r'\[\d+\]$','',block.get('instance'));assert kind==pb.get('name'),(kind,pb.get('name'))
 model=pb.get('blif_model')
 if model:
  assert not list(block.findall('block'));counts[model]+=1
  if 'DFF_PP' in model:records.append(dict(name=block.get('name'),model=model,instance=block.get('instance')))
  return
 scope=pb
 if block.get('mode') is not None:
  choices=[mode for mode in pb.findall('mode') if mode.get('name')==block.get('mode')];assert len(choices)==1;scope=choices[0]
 children={child.get('name'):child for child in scope.findall('pb_type')}
 for child in block.findall('block'):
  if child.get('name')=='open':continue
  name=re.sub(r'\[\d+\]$','',child.get('instance'));assert name in children;visit(child,children[name])
for block in packed.findall('block'):
 if block.get('name')=='open':continue
 name=re.sub(r'\[\d+\]$','',block.get('instance'));assert name in top;visit(block,top[name])
assert counts['.latch']==1586 and counts['.subckt $_DFF_PP0_']==54 and counts['.subckt $_DFF_PP1_']==4
bindings={str(p):sha(p) for p in (Path(__file__).resolve(),B/'receipt.json',B/'protocol.json',B/'design.net',arch)}
D.mkdir(exist_ok=False);(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,models=dict(counts),reset_records=records,scope='Packed architecture-selected primitive model census, all ordinary/reset FF counts preserved. No reset-pin connectivity tracing, sequential functional proof, placement/routing label or characterized timing claim.'),indent=2)+'\n');print(dict(models=dict(counts),reset_records=len(records)),flush=True)
