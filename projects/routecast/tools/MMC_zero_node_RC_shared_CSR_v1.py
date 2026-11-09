"""Pinned MMC zero-node-RC XML to shared physical-edge CSR, no labels."""
import time,xml.etree.ElementTree as ET
from array import array
from fractions import Fraction

def load(graph):
  caps=array('I');kinds=[];dest=array('I');costs=array('Q');offsets=array('Q');switches={};stack=[];last_source=-1;setup=time.perf_counter()
  for event,e in ET.iterparse(graph,events=('start','end')):
   if event=='start':stack.append(e);continue
   parent=stack[-2].tag if len(stack)>1 else None
   if e.tag=='node' and parent=='rr_nodes':
    assert int(e.get('id'))==len(caps);caps.append(int(e.get('capacity')));kinds.append(e.get('type'));t=e.find('timing');assert Fraction(t.get('R'))==Fraction(t.get('C'))==0
   elif e.tag=='switch' and parent=='switches':
    t=e.find('timing');assert Fraction(t.get('Cinternal','0'))==0 and e.get('type') in ['buffer','mux','tristate'];value=Fraction(t.get('Tdel','0'))*10**18;assert value.denominator==1 and 0<=value<2**64;switches[int(e.get('id'))]=int(value)
   elif e.tag=='edge' and parent=='rr_edges':
    u,v,s=(int(e.get(k)) for k in ['src_node','sink_node','switch_id']);assert u>=last_source;last_source=u
    while len(offsets)<=u:offsets.append(len(dest))
    dest.append(v);costs.append(switches[s])
   if (e.tag,parent) in [('node','rr_nodes'),('switch','switches'),('edge','rr_edges')]:stack[-2].remove(e);e.clear()
   stack.pop()
  while len(offsets)<=len(caps):offsets.append(len(dest))
  assert len(caps)==904438 and len(dest)==8097539 and len(offsets)==len(caps)+1;graph_seconds=time.perf_counter()-setup
  return offsets,dest,costs,caps,kinds,graph_seconds
