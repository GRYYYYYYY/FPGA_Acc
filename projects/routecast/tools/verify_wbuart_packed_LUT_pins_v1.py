"""Audit all LUT atom identities and logical input rotations, without inventing packed truth tables."""
import hashlib,json,re,xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 pack=R/'experiments/wbuart_pack_v1_2026-10-20';net=pack/'design.net';blif=pack/'design.blif';proof=R/'experiments/wbuart_packed_FF_v1_2026-10-20/verification.json'
 admission=json.loads(proof.read_text())
 for p,h in admission['bindings'].items():assert sha(Path(p))==h
 bindings={str(p):sha(p) for p in [net,blif,proof,Path(__file__)]}
 root=ET.parse(net).getroot();parent={c:b for b in root.iter('block') for c in b.findall('block')};memo={}
 def signal(block,port,index,active=frozenset()):
  key=(block,port,index);assert key not in active,'pin cycle'
  if key in memo:return memo[key]
  ports=[p for section in ['inputs','outputs','clocks'] for p in block.findall(section+'/port') if p.get('name')==port];assert len(ports)==1
  value=ports[0].text.split()[index]
  if '->' in value:
   ref=value.split('->',1)[0];match=re.fullmatch(r'([^.]*)\.([^.[\]]+)\[(\d+)\]',ref);assert match,ref
   inst,pin,bit=match.groups();scope=block;target=None
   while scope is not None:
    children=[c for c in scope.findall('block') if c.get('instance')==inst]
    if children:assert len(children)==1;target=children[0];break
    own=scope.get('instance');
    if inst in [own,re.sub(r'\[\d+\]$','',own)]:target=scope;break
    scope=parent.get(scope)
   assert target is not None,ref
   value=signal(target,pin,int(bit),active|{key})
  memo[key]=value;return value
 lines=[];pending=''
 for line in blif.read_text().splitlines():
  line=line.strip()
  if not line or line.startswith('#'):continue
  if line.endswith('\\'):pending+=line[:-1]+' ';continue
  lines.append((pending+line).split());pending=''
 assert not pending
 atoms={}
 for t in lines:
  if t[0]=='.names':assert t[-1] not in atoms;atoms[t[-1]]=t[1:-1]
 observed={};rotations=0
 for b in root.iter('block'):
  if b.get('name')=='open' or b.findall('block') or b.get('instance')!='lut[0]':continue
  name=b.get('name');assert name in atoms and name not in observed,name
  inp=b.findall('inputs/port');maps=b.findall('inputs/port_rotation_map');outs=b.findall('outputs/port');assert len(inp)==len(maps)==len(outs)==1
  tokens=inp[0].text.split();rotation=maps[0].text.split();assert len(tokens)==len(rotation)
  expected=atoms[name];actual={}
  for i,(token,logical) in enumerate(zip(tokens,rotation)):
   if logical=='open':assert token=='open';continue
   j=int(logical);assert j not in actual and token!='open';actual[j]=signal(b,inp[0].get('name'),i)
  assert set(actual)==set(range(len(expected))),(name,actual,expected)
  assert [actual[i] for i in range(len(expected))]==expected,(name,actual,expected)
  assert signal(b,outs[0].get('name'),0)==name
  rotations+=any(int(x)!=i for i,x in enumerate(rotation) if x!='open');observed[name]=dict(inputs=expected,physical_to_logical=rotation)
 assert set(observed)==set(atoms),(len(observed),len(atoms),set(atoms)-set(observed))
 for p,h in bindings.items():assert sha(Path(p))==h
 out=R/'experiments/wbuart_packed_LUT_pins_v1_2026-10-20';out.mkdir(exist_ok=False)
 with (out/'verification.json').open('x') as f:json.dump(dict(status='all_packed_LUT_logical_inputs_outputs_and_rotations_verified',bindings=bindings,LUT_atoms=len(observed),nonidentity_physical_maps=rotations,atoms=observed,scope='All mapped BLIF .names atoms matched bijectively to packed LUT leaves; every logical input resolved through physical rotation and packed hierarchy, exact output identity. Packed XML contains no truth tables; this checks preservation of LUT atom references and wiring, not an independent packed truth-table simulation, original HDL/four-state or timing equivalence.',strict_unseen_admitted=False,new_route_labels=False),f,indent=2)
 print('PACKED LUT PIN PASS',len(observed),'nonidentity maps',rotations)
if __name__=='__main__':main()
