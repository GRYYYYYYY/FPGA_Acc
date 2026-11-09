"""Trace all retained native RAM bit-atom pins through actual packed hierarchy."""
import json,re,xml.etree.ElementTree as ET
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments'
B=E/'full_native_ram_pack_v2_2026-10-09';S=E/'full_ram_native_slices_v1_2026-10-09'
D=E/'full_native_ram_packed_pins_v1_2026-10-09'
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
expected={}
for line in lines:
 if not line.startswith('.subckt dual_port_ram '):continue
 pairs=dict(word.split('=') for word in line.split()[2:]);key=canon(pairs['out2'])
 assert key not in expected;expected[key]=pairs
records=[]
for block in root.iter('block'):
 if block.get('name')=='open' or not re.fullmatch(r'memory_slice(?:_1bit)?\[\d+\]',block.get('instance','')):continue
 output=pin(block,'out2',0);key=canon(output);assert key in expected
 pairs=expected[key];actual={}
 for port in ('addr1','addr2'):
  for i in range(10):actual[f'{port}[{i}]']=pin(block,port,i)
 for port in ('data1','data2','we1','we2','clk','out2'):actual[port]=pin(block,port,0)
 for port,value in actual.items():assert canon(value)==canon(pairs[port]),(key,port,value,pairs[port])
 assert (block.find("outputs/port[@name='out1']").text or '').strip()=='open'
 records.append(dict(output=output,actual=actual,expected={p:pairs[p] for p in actual}))
assert len(records)==174 and len({canon(r['output']) for r in records})==174
D.mkdir(exist_ok=False)
paths=[Path(__file__).resolve(),proof,B/'receipt.json',B/'design.net',S/'design.blif']
report=dict(passed=True,bindings={str(p):sha(p) for p in paths},ram_bit_atoms=174,pins_checked=174*26,records=records,
 scope='All retained RAM bit-atom address/data/write-enable/clock/read-output packed terminal identities modulo actual BLIF identity buffers. Not functional collision model, physical initial configuration or Full sequential equivalence.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',report['pins_checked'],'RAM pins')
