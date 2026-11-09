"""Independent complete JSON-to-cut port, gate truth table and sequential-boundary audit."""
import itertools,json
from collections import Counter

def audit(module,text,boundary):
 blocks={};inputs=None;outputs=None;current=None
 for raw in text.splitlines():
  words=raw.split()
  if not words or words[0].startswith('#'):continue
  if words[0]=='.inputs':assert inputs is None;inputs=words[1:];current=None
  elif words[0]=='.outputs':assert outputs is None;outputs=words[1:];current=None
  elif words[0]=='.names':
   name=words[-1];assert name not in blocks;blocks[name]=(words[1:-1],[]);current=name
  elif words[0] in ('.model','.end'):current=None
  else:
   assert current is not None;blocks[current][1].append(words)
 sequential={name:cell for name,cell in module['cells'].items() if cell['type'] in ('$_DFF_P_','$_DFF_N_','$_DFF_PP0_','$_DFF_PP1_')}
 assert boundary==dict(cells=sequential,ports=module['ports'])
 def token(bit):
  assert type(bit) is int or bit in ('0','1')
  return 'b'+str(bit) if type(bit) is int else 'const'+bit
 ins=set();outs=set()
 for port in module['ports'].values():
  assert port['direction'] in ('input','output')
  (ins if port['direction']=='input' else outs).update(token(bit) for bit in port['bits'])
 for cell in sequential.values():
  assert set(cell['connections'])==({'C','D','Q'} if cell['type'] in ('$_DFF_P_','$_DFF_N_') else {'C','D','Q','R'})
  for port,bits in cell['connections'].items():
   assert len(bits)==1 and cell['port_directions'][port]==('output' if port=='Q' else 'input')
   (ins if port=='Q' else outs).add(token(bits[0]))
 ins-={'const0','const1'};assert set(inputs)==ins and len(inputs)==len(ins)
 assert set(outputs)==outs and len(outputs)==len(outs)
 assert blocks['const0']==([],[]) and blocks['const1']==([],[['1']])
 logic={name:cell for name,cell in module['cells'].items() if name not in sequential};expected={'const0','const1'};truth_cases=0
 for cell in logic.values():
  kind=cell['type'];ports=['A','B','S'] if kind=='$_MUX_' else ['A'] if kind=='$_NOT_' else ['A','B']
  assert kind in ('$_MUX_','$_NOT_','$_OR_','$_AND_','$_XOR_')
  assert set(cell['connections'])==set(ports+['Y'])
  assert all(len(bits)==1 for bits in cell['connections'].values())
  assert all(cell['port_directions'][port]==('output' if port=='Y' else 'input') for port in ports+['Y'])
  name=token(cell['connections']['Y'][0]);assert name not in expected;expected.add(name)
  args,rows=blocks[name];assert args==[token(cell['connections'][port][0]) for port in ports]
  for pattern in rows:assert len(pattern)==2 and pattern[1]=='1' and len(pattern[0])==len(ports) and set(pattern[0])<=set('01-')
  for vector in itertools.product((False,True),repeat=len(ports)):
   actual=any(all(bit=='-' or (bit=='1')==value for bit,value in zip(pattern[0],vector)) for pattern in rows)
   a=vector[0];b=vector[1] if len(vector)>1 else False
   if kind=='$_MUX_':expected_value=(a and not vector[2]) or (b and vector[2])
   elif kind=='$_NOT_':expected_value=not a
   elif kind=='$_OR_':expected_value=a or b
   elif kind=='$_AND_':expected_value=a and b
   else:expected_value=a!=b
   assert actual==expected_value;truth_cases+=1
 assert set(blocks)==expected
 available=ins|{'const0','const1'};pending={name:set(args) for name,(args,_) in blocks.items() if name not in available}
 while pending:
  ready={name for name,deps in pending.items() if deps<=available};assert ready,'undeclared input or combinational cycle'
  available|=ready
  for name in ready:del pending[name]
 assert outs<=available
 return dict(logic_cells=len(logic),truth_cases=truth_cases,sequential_cells=len(sequential),async_reset_cells=sum(cell['type'] in ('$_DFF_PP0_','$_DFF_PP1_') for cell in sequential.values()),cut_inputs=len(ins),cut_outputs=len(outs))
