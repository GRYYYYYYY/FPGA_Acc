"""Single authenticated XML pass for immutable physical and exact electrical inventories."""
from dataclasses import dataclass
from types import MappingProxyType
import xml.etree.ElementTree as ET
from path_rc import number
from pre_route_endpoints import sha
from native_route_audit_cache import Snapshot
@dataclass(frozen=True)
class Inventory:
 physical: Snapshot
 node_classes: tuple
 classes: tuple
 electrical_switches: object
 digest: str

def read(path,expected):
 if sha(path)!=expected:raise ValueError('Graph binding changed')
 nodes={};arcs={};indices=[];classes=[];lookup={};switches={};edges=0;stack=[]
 for event,e in ET.iterparse(path,events=('start','end')):
  if event=='start':
   stack.append(e)
   if len(stack)==1 and e.tag!='rr_graph':raise ValueError('Expected RR root')
   continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and parent=='rr_nodes':
   nid=int(e.get('id'))
   if nid!=len(indices):raise ValueError('Contiguous unique node IDs required')
   nodes[nid]=(e.get('type'),e.get('capacity'))
   timing=e.find('timing')
   if timing is None or not {'R','C'}<=set(timing.attrib):raise ValueError('Missing node RC')
   key=(timing.get('R'),timing.get('C'))
   if key not in lookup:
    lookup[key]=len(classes);classes.append(tuple(map(number,key)))
   indices.append(lookup[key])
  elif e.tag=='switch' and parent=='switches':
   sid=int(e.get('id'));timing=e.find('timing')
   if sid<0 or sid in switches or timing is None:raise ValueError('Invalid switch')
   if e.get('type') not in {'buffer','mux','tristate'}:raise ValueError('Nonbuffered switch')
   if number(timing.get('Cinternal','0')):raise ValueError('Nonzero Cinternal')
   switches[sid]=(number(timing.get('R','0')),number(timing.get('Tdel','0')))
  elif e.tag=='edge' and parent=='rr_edges':
   key=tuple(int(e.get(k)) for k in ('src_node','sink_node','switch_id'))
   arcs.setdefault(key,edges);edges+=1
  if (e.tag,parent) in {('node','rr_nodes'),('edge','rr_edges'),('switch','switches'),('segment','segments')}:
   stack[-2].remove(e);e.clear()
  stack.pop()
 if not indices or not switches:raise ValueError('Empty electrical context')
 if sha(path)!=expected:raise ValueError('Graph changed during unified read')
 physical=Snapshot(MappingProxyType(nodes),frozenset(),MappingProxyType(arcs),frozenset(switches),edges)
 return Inventory(physical,tuple(indices),tuple(classes),MappingProxyType(switches),expected)
