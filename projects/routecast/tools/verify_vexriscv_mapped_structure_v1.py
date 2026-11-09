"""Independent exact mapped-body, original IO and sequential connectivity audit."""
import json
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'vexriscv_mapped_structure_v2_2026-10-09';D=E/'vexriscv_mapped_structure_verification_v1_2026-10-09';D.mkdir(exist_ok=False)
def logical(text):
 result=[];pending=[]
 for raw in text.splitlines():
  words=raw.split()
  if not words or words[0].startswith('#'):continue
  continued=words[-1]==chr(92)
  pending.extend(words[:-1] if continued else words)
  if not continued:result.append(pending);pending=[]
 assert not pending;return result
def parse(text):
 names=[];latches=[];sub=[];inputs=[];outputs=[];current=None;model=0
 for words in logical(text):
  if words[0]=='.model':model+=1;current=None
  elif words[0]=='.end':current=None
  elif model!=1:continue
  elif words[0]=='.inputs':inputs.extend(words[1:]);current=None
  elif words[0]=='.outputs':outputs.extend(words[1:]);current=None
  elif words[0]=='.names':current=[tuple(words[1:]),[]];names.append(current)
  elif words[0]=='.latch':latches.append(tuple(words[1:]));current=None
  elif words[0]=='.subckt':sub.append((words[1],tuple(sorted(words[2:]))));current=None
  else:assert current is not None;current[1].append(tuple(words))
 return inputs,outputs,Counter((args,tuple(rows)) for args,rows in names),Counter(latches),Counter(sub)
p=E/'vexriscv_flattened_candidate_v1_2026-10-09/design.json';original=json.loads(p.read_text())['modules']['VexRiscvSmallest'];mapped=E/'vexriscv_cut_logic_v1_2026-10-09/mapped.blif';ins,outs,body,_,_=parse(mapped.read_text());actual=parse((B/'design.blif').read_text());expected_inputs=[];expected_outputs=[];aliases=Counter()
def bit(n):return 'b'+str(n) if type(n)is int else 'const'+n
for label,port in original['ports'].items():
 for index,n in enumerate(port['bits']):
  name=label if len(port['bits'])==1 else label+'['+str(index)+']'
  if port['direction']=='input':expected_inputs.append(name);args=(name,bit(n))
  else:expected_outputs.append(name);args=(bit(n),name)
  aliases[args,(('1','1'),)]+=1
assert actual[0]==expected_inputs and actual[1]==expected_outputs
assert actual[2]==body+aliases
latches=Counter();sub=Counter()
for cell in original['cells'].values():
 kind=cell['type']
 if not kind.startswith('$_DFF'):continue
 connections={key:bit(bits[0]) for key,bits in cell['connections'].items()}
 if kind=='$_DFF_P_':latches[connections['D'],connections['Q'],'re',connections['C'],'2']+=1
 else:sub[kind,tuple(sorted(key+'='+value for key,value in connections.items()))]+=1
assert actual[3]==latches and actual[4]==sub
reload=json.loads((B/'reload.json').read_text())['modules']['VexRiscvSmallest']
def wire(token):
 if token in ('const0','const1'):return token[-1]
 return reload['netnames'][token]['bits'][0]
plain=Counter();resets=Counter()
for cell in reload['cells'].values():
 if cell['type']=='$dff':
  assert int(cell['parameters']['CLK_POLARITY'],2)==1 and int(cell['parameters']['WIDTH'],2)==1
  plain[tuple(cell['connections'][key][0] for key in ('D','Q','CLK'))]+=1
 elif cell['type'] in ('$_DFF_PP0_','$_DFF_PP1_'):
  resets[cell['type'],tuple(sorted((key,bits[0]) for key,bits in cell['connections'].items()))]+=1
 else:assert cell['type']=='$lut'
assert plain==Counter((wire(d),wire(q),wire(c)) for d,q,mode,c,init in latches.elements())
expected=Counter()
for (kind,ports),count in sub.items():expected[kind,tuple(sorted((key,wire(value)) for key,value in (pair.split('=') for pair in ports)))]+=count
assert resets==expected
bindings=closure([Path(__file__)])
for path in (p,mapped,B/'design.blif',B/'reload.json',B/'receipt.json'):bindings[str(path)]=sha(path)
receipt=json.loads((B/'receipt.json').read_text());assert all(sha(path)==digest for path,digest in receipt['bindings'].items());bindings.update(receipt['bindings'])
report=dict(bindings=bindings,plain_flops=sum(plain.values()),reset_flops=sum(resets.values()),top_inputs=len(actual[0]),top_outputs=len(actual[1]),mapped_body_and_aliases_exact=True,sequential_readback_exact=True,scope='Independent structural full top IO/mapped combinational-body equality and original sequential-pin/type readback. No full HDL sequential equivalence or characterized async reset timing claim.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print({key:value for key,value in report.items() if key!='bindings'},flush=True)
