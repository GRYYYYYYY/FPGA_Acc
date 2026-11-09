"""Explicit architecture non-clock-global receiver binding, independent of routes."""
import xml.etree.ElementTree as ET
import re

def classify(mapping,packed,architecture,graph):
 blocks={};depth=0
 for event,e in ET.iterparse(packed,events=('start','end')):
  if event=='start':depth+=1;continue
  if depth==2 and e.tag=='block':
   name=e.get('name')
   if name in blocks:raise ValueError('duplicate packed block')
   blocks[name]=re.sub(r'\[\d+\]$','',e.get('instance'));e.clear()
  depth-=1
 declarations={}
 for tile in ET.parse(architecture).getroot().findall('./tiles/tile'):
  for sub in tile.findall('./sub_tile'):
   for port in sub.findall('./input'):
    if port.get('is_non_clock_global','false').lower() not in ('true','1'):continue
    for site in sub.findall('./equivalent_sites/site'):
     key=(site.get('pb_type'),port.get('name'))
     if key in declarations:raise ValueError('ambiguous global port binding')
     declarations[key]={'tile':tile.get('name'),'sub_tile':sub.get('name'),'port':port.get('name'),'num_pins':int(port.get('num_pins'))}
 rr={}
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start' and e.tag=='rr_nodes':break
  if event=='end' and e.tag=='block_type':
   tile=e.get('name')
   for class_index,cls in enumerate(e.findall('./pin_class')):
    for pin in cls.findall('./pin'):
     match=re.fullmatch(r'(.+?)(?:\[(\d+)\])?\.([^\[]+)\[(\d+)\]',(pin.text or '').strip())
     if match:
      kind,instance,port,bit=match.groups();key=(tile,kind,int(instance or 0),port,int(bit))
      if key in rr:raise ValueError('duplicate RR physical pin')
      rr[key]=(int(pin.get('ptc')),class_index,cls.get('type'))
   e.clear()
 result=[]
 for row in mapping['pin_details']:
  if row['role']!='SINK':continue
  kind=blocks[row['block']];decl=declarations.get((kind,row['port']))
  if decl is None:continue
  # Explicitly support one physical sub-tile instance; reject unsupported binding.
  matches=[v for k,v in rr.items() if k[0]==decl['tile'] and k[1]==kind and k[3]==row['port'] and k[4]==row['bit'] and v[0]==row['physical_pin_ptc']]
  if len(matches)!=1 or matches[0][1]!=row['class_id'] or matches[0][2]!='INPUT':raise ValueError('unverified global physical pin binding')
  result.append({'net_id':row['net_id'],'net':row['net'],'block':row['block'],'port':row['port'],'bit':row['bit'],'physical_pin_ptc':row['physical_pin_ptc'],'class_id':row['class_id'],'rr_node':row['rr_node'],'declaration':decl})
 return result
