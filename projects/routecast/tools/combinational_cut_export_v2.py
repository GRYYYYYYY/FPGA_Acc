"""Reusable flattened gate cut export; all sequential cells retained verbatim."""
import itertools
def export(m):
 assert all(p['direction'] in ('input','output') for p in m['ports'].values()),'inout requires explicit bidirectional lowering'
 sequential={name:cell for name,cell in m['cells'].items() if cell['type'].startswith('$_DFF')};logic={name:cell for name,cell in m['cells'].items() if name not in sequential}
 inputs=set();outputs=set()
 for port in m['ports'].values():
  (inputs if port['direction']=='input' else outputs).update(port['bits'])
 for cell in sequential.values():
  for port,bits in cell['connections'].items():(inputs if cell['port_directions'][port]=='output' else outputs).update(bits)
 assert all(type(bit) is int or bit in ('0','1') for bit in inputs|outputs)
 name=lambda bit:f'b{bit}' if type(bit) is int else f'const{bit}'
 inputs={bit for bit in inputs if type(bit) is int}
 lines=['.model vex_cut','.inputs '+' '.join(name(bit) for bit in sorted(inputs)),'.outputs '+' '.join(name(bit) for bit in sorted(outputs,key=str)),'.names const0','.names const1','1']
 truth={'$_MUX_':(['A','B','S'],lambda v:v[1] if v[2] else v[0]),'$_NOT_':(['A'],lambda v:1-v[0]),'$_OR_':(['A','B'],lambda v:v[0]|v[1]),'$_AND_':(['A','B'],lambda v:v[0]&v[1]),'$_XOR_':(['A','B'],lambda v:v[0]^v[1])}
 for cell in logic.values():
  ports,fn=truth[cell['type']];assert all(len(bits)==1 for bits in cell['connections'].values())
  args=[name(cell['connections'][port][0]) for port in ports];out=name(cell['connections']['Y'][0]);lines.append('.names '+' '.join(args+[out]))
  for vector in itertools.product((0,1),repeat=len(ports)):
   if fn(vector):lines.append(''.join(map(str,vector))+' 1')
 lines.append('.end')
 return '\n'.join(lines)+'\n',dict(cells=sequential,ports=m['ports'])
