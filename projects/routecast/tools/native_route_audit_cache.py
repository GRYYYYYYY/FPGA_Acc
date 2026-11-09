"""Serial three-entry immutable RR inventory for independent route audit.

Every call authenticates graph bytes; route-dependent state remains local.
Entry count is not an RSS bound, and no concurrent publication is provided.
"""
from collections import OrderedDict
from types import MappingProxyType
from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET
from pre_route_endpoints import sha
@dataclass(frozen=True)
class Snapshot:
 nodes:object
 duplicate_nodes:frozenset
 arcs:object
 switches:frozenset
 edge_count:int
_CACHE=OrderedDict();STATS=dict(builds=0,hits=0,evictions=0)
def clear_cache():
 _CACHE.clear()
 for k in STATS:STATS[k]=0

def snapshot(path,expected):
 if sha(path)!=expected:raise ValueError('graph binding changed')
 key=(str(Path(path).resolve()),expected)
 if key in _CACHE:
  STATS['hits']+=1;_CACHE.move_to_end(key);return _CACHE[key]
 nodes={};duplicates=set();arcs={};switches=set();edge_count=0;stack=[]
 for event,e in ET.iterparse(path,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='switch' and parent=='switches':switches.add(int(e.attrib['id']))
  if e.tag=='node' and parent=='rr_nodes':
   nid=int(e.attrib['id'])
   if nid in nodes:duplicates.add(nid)
   else:nodes[nid]=(e.attrib.get('type'),e.attrib.get('capacity'))
  if e.tag=='edge' and parent=='rr_edges':
   arc=tuple(int(e.attrib[k]) for k in ('src_node','sink_node','switch_id'));arcs.setdefault(arc,edge_count);edge_count+=1
  if (e.tag,parent) in {('node','rr_nodes'),('edge','rr_edges'),('switch','switches')}:stack[-2].remove(e);e.clear()
  stack.pop()
 if sha(path)!=expected:raise ValueError('graph changed during inventory build')
 value=Snapshot(MappingProxyType(nodes),frozenset(duplicates),MappingProxyType(arcs),frozenset(switches),edge_count);_CACHE[key]=value;STATS['builds']+=1
 if len(_CACHE)>3:_CACHE.popitem(last=False);STATS['evictions']+=1
 return value
