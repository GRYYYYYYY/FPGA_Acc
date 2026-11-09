"""Explicit pad I/O/enable lowering for single-driver active-high mux-with-Z boundaries."""
import copy

def lower(module):
 result=copy.deepcopy(module);pads={bit for p in module['ports'].values() if p['direction']=='inout' for bit in p['bits']};drivers={};records=[];remove=set()
 for name,cell in module['cells'].items():
  for port,bits in cell['connections'].items():
   if cell['port_directions'][port]!='output':continue
   for index,bit in enumerate(bits):
    if bit in pads:drivers.setdefault(bit,[]).append((name,port,index))
 for label,port in module['ports'].items():
  if port['direction']!='inout':continue
  assert len(set(port['bits']))==len(port['bits'])
  data=[];enable=[]
  for bit in port['bits']:
   assert type(bit)==int and len(drivers.get(bit,[]))==1,'pad must have exactly one internal driver'
   name,out,index=drivers[bit][0];cell=module['cells'][name];c=cell['connections'];assert cell['type']=='$mux' and out=='Y';assert set(c)=={'A','B','S','Y'} and len(c['S'])==1
   assert len(c['A'])==len(c['B'])==len(c['Y']);assert all(b in pads for b in c['Y']),'mixed pad/internal mux not supported'
   assert c['A'][index]=='z' and c['B'][index]!='z','only active-high Z/data mux supported'
   data.append(c['B'][index]);enable.append(c['S'][0]);remove.add(name);records.append(dict(port=label,pad_bit=bit,cell=name,driver_index=index,data=c['B'][index],enable=c['S'][0],disabled='z'))
  del result['ports'][label]
  for suffix,direction,bits in (('__pad_in','input',port['bits']),('__pad_out','output',data),('__pad_oe','output',enable)):
   key=label+suffix;assert key not in result['ports'];result['ports'][key]=dict(direction=direction,bits=bits)
 for name in remove:del result['cells'][name]
 assert {r['pad_bit'] for r in records}==pads
 return result,records
