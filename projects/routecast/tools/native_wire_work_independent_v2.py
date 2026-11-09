"""Independent lexical iteration counters and originalXML wire-span accounting."""
from pathlib import Path
from collections import Counter
from array import array
import xml.etree.ElementTree as E
import struct
from pre_route_endpoints import sha

def read_spans(graph,digest):
 graph=Path(graph)
 if sha(graph)!=digest:raise ValueError('graph identity changed')
 spans=array('I');stack=[]
 for event,e in E.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and parent=='rr_nodes':
   assert int(e.get('id'))==len(spans);length=0
   if e.get('type') in ['CHANX','CHANY']:
    direction=e.get('direction');assert direction in ['INC_DIR','DEC_DIR','BI_DIR','NO_DIR'];loc=e.find('loc')
    if direction!='NO_DIR':length=1+int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'));assert length>0
   spans.append(length);stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 assert sha(graph)==digest
 return spans

def audit(log,route,physical,spans):
 table=[];successful=[];printed_wire=[];heap_total=None;rounded=[];totals=None
 for line in Path(log).read_text().splitlines():
  w=line.split()
  if w[:2]==['Router','Stats:']:
   assert totals is None
   fields={w[i].rstrip(':'):int(w[i+1]) for i in range(2,len(w)-1,2)};totals=fields;heap_total=fields['total_heap_pushes']
  if line.strip().startswith('Successfully routed after '):successful.append(int(w[3]))
  if line.strip().startswith('Total wirelength: ') and len(w)>2 and w[2].rstrip(',').isdigit():printed_wire.append(int(w[2].rstrip(',')))
  if len(w)>=9 and w[8].startswith('('):
   try:ints=[int(w[i]) for i in [0,3,5,6,7]];float(w[1]);float(w[2])
   except ValueError:continue
   table.append(dict(iteration=ints[0],BB_updates=ints[1],heap_pushes=int(w[4]) if w[4].isdigit() else None,rerouted_NET_operations=ints[2],rerouted_connection_operations=ints[3],overused_RR_nodes=ints[4]))
   if table[-1]['heap_pushes'] is None:rounded.append((len(table)-1,w[4]))
 assert totals is not None and len(rounded)<=1
 if rounded:
  index,token=rounded[0];remaining=heap_total-sum(r['heap_pushes'] for r in table if r['heap_pushes'] is not None);assert remaining>9999999
  assert format(struct.unpack('f',struct.pack('f',remaining))[0],'#.2g')==token
  table[index]['heap_pushes']=remaining
 assert sum(r['heap_pushes'] for r in table)==heap_total
 assert sum(r['rerouted_NET_operations'] for r in table)==totals['total_nets_routed']
 assert sum(r['rerouted_connection_operations'] for r in table)==totals['total_connections_routed']
 assert len(successful)==len(printed_wire)==1 and [r['iteration'] for r in table]==list(range(1,successful[0]+1)) and table[-1]['overused_RR_nodes']==0
 unions={};current=None
 with Path(route).open() as f:
  for line in f:
   w=line.split()
   if w and w[0]=='Net':
    current=int(w[1]) if line.rstrip().endswith(')') else None
    if current is not None:assert current not in unions;unions[current]=set()
   elif w and w[0]=='Node:':assert current is not None;unions[current].add(int(w[1]))
 occupancy=Counter(n for nodes in unions.values() for n in nodes);assert dict(occupancy)=={int(n):v for n,v in physical['node_occupancy'].items()} and len(unions)==physical['routed_nets']==55300
 wire=sum(spans[n]*count for n,count in occupancy.items());assert wire==printed_wire[0]
 return dict(iterations=len(table),wirelength=wire,heap_pushes=sum(r['heap_pushes'] for r in table),rerouted_NET_operations=sum(r['rerouted_NET_operations'] for r in table),rerouted_connection_operations=sum(r['rerouted_connection_operations'] for r in table),rows=table)
