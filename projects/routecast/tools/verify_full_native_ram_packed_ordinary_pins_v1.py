"""Trace packed hierarchical pin references to terminal net names, with BLIF buffer aliases."""
import json,re,xml.etree.ElementTree as ET
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'full_native_ram_pack_v2_2026-10-09';S=E/'full_native_ram_blif_v1_2026-10-09';D=E/'full_native_ram_packed_ordinary_pins_v1_2026-10-09'
proof=E/'full_native_ram_packed_models_v1_2026-10-09/verification.json'
for path in (B/'receipt.json',proof):
 receipt=json.loads(path.read_text())
 for p,h in receipt['bindings'].items():assert sha(p)==h
root=ET.parse(B/'design.net').getroot();parents={c:b for b in root.iter('block') for c in b.findall('block')}
uf={}
def canon(x):
 if x not in uf:uf[x]=x
 if uf[x]!=x:uf[x]=canon(uf[x])
 return uf[x]
lines=(S/'design.blif').read_text().splitlines()
for i,line in enumerate(lines[:-1]):
 w=line.split()
 if len(w)==3 and w[0]=='.names' and lines[i+1].split()==['1','1']:uf[canon(w[2])]=canon(w[1])
def pin(block,port,index,seen=None):
 seen=set() if seen is None else seen;key=(id(block),port,index);assert key not in seen;seen.add(key)
 found=[p for tag in ('inputs','outputs','clocks') for p in block.findall(tag+'/port') if p.get('name')==port];assert len(found)==1
 words=(found[0].text or '').split();assert index<len(words);token=words[index];assert token!='open'
 if '->' not in token:return token
 ref=token.split('->',1)[0];m=re.fullmatch(r'([^.]+)\.([^\[]+)\[(\d+)\]',ref);assert m,ref
 instance,sourceport,idx=m.groups();parent=parents[block]
 if instance==block.get('instance') or instance==re.sub(r'\[\d+\]$','',block.get('instance','')):source=block
 elif instance==parent.get('instance') or instance==re.sub(r'\[\d+\]$','',parent.get('instance','')):source=parent
 else:
  scope=block if found[0] in list(block.find('outputs')) else parent
  choices=[c for c in scope.findall('block') if c.get('instance')==instance];assert len(choices)==1,(ref,scope.attrib);source=choices[0]
 return pin(source,sourceport,int(idx),seen)
expected={x['ports']['Q']:x for x in json.loads((S/'reconstruction_records.json').read_text())['sequential'] if x['type']=='$_DFF_P_'};records=[]
for block in root.iter('block'):
 if block.get('name')=='open' or block.get('instance')!='storage[0]' or parents[block].get('mode')!='ordinary':continue
 q=pin(block,'Q',0);assert q in expected;ref=expected[q]
 actual={p:pin(block,p,0) for p in ('D','Q','clk')}
 for p,v in actual.items():assert canon(v)==canon(ref['ports']['C' if p=='clk' else p])
 records.append(dict(q=q,actual=actual,expected=ref['ports'],source_init=ref['init'],packed_parameters=[(e.tag,e.attrib,e.text) for e in block.findall('parameters/*')]))
assert len(records)==2100 and len({r['q'] for r in records})==2100
assert sum(r['source_init']=='0' for r in records)==13
D.mkdir(exist_ok=False);paths=[Path(__file__).resolve(),proof,B/'receipt.json',B/'design.net',S/'reconstruction_records.json',S/'design.blif'];report=dict(bindings={str(p):sha(p) for p in paths},ordinary_flops=2100,pins_checked=6300,initialized_control_flops=13,physical_initialization_proven=False,records=records,scope='Packed ordinary D/Q/clk terminal identity; 13 initialized controls connected. Packed storage parameters have no initialization encoding; physical initialization is not established. Not HDL sequential equivalence, timing characterization or architecture interconnect legality proof.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS 2100 ordinary FFs / 6300 pins; physical init not proven')
