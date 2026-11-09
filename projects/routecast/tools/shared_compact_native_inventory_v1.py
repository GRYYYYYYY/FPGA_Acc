"""One authenticated compact XML load for whole-NET selection and native binding."""
from array import array
from pathlib import Path
from types import SimpleNamespace,MappingProxyType
import xml.etree.ElementTree as ET
from pre_route_endpoints import sha
from prepared_csr import TYPES
from streaming_prediction_audit import Nodes
from immutable_xml_prediction_audit import CompactEdges
class NativeEdges:
 def __init__(self,edges):self.raw=edges
 def __len__(self):return len(self.raw)
 def __getitem__(self,index):
  if isinstance(index,slice):return [self[i] for i in range(*index.indices(len(self)))]
  if not 0<=index<len(self):raise IndexError(index)
  e=self.raw[index];return e.source,e.sink,e.switch_id
class Inventory:
 def __init__(self,path):
  self.path=Path(path);self.digest=sha(self.path);types=array('B');caps=array('Q');sources=array('Q');dest=array('Q');switch=array('Q');locations=[];stack=[]
  for event,e in ET.iterparse(self.path,events=('start','end')):
   if event=='start':
    stack.append(e)
    if len(stack)==1 and e.tag!='rr_graph':raise ValueError('expected RR root')
    continue
   parent=stack[-2].tag if len(stack)>1 else None
   if e.tag=='node' and parent=='rr_nodes':
    if int(e.get('id'))!=len(types):raise ValueError('contiguous ascending node IDs required')
    kind=e.get('type');capacity=int(e.get('capacity'));loc=e.find('loc')
    if kind not in TYPES or capacity<0 or loc is None:raise ValueError('invalid node')
    types.append(TYPES[kind]);caps.append(capacity);locations.append(MappingProxyType(dict(loc.attrib)))
   elif e.tag=='edge' and parent=='rr_edges':
    sources.append(int(e.get('src_node')));dest.append(int(e.get('sink_node')));switch.append(int(e.get('switch_id')))
   if (e.tag,parent) in (('node','rr_nodes'),('edge','rr_edges'),('switch','switches'),('segment','segments')):stack[-2].remove(e);e.clear()
   stack.pop()
  if any(n>=len(types) for n in sources) or any(n>=len(types) for n in dest):raise ValueError('invalid arc node')
  if sha(self.path)!=self.digest:raise ValueError('graph changed during parse')
  compact=CompactEdges(sources,dest,switch);self.graph=SimpleNamespace(nodes=Nodes(memoryview(types.tobytes()),memoryview(caps.tobytes()).cast('Q')),edges=compact,sha256=self.digest)
  kinds={v:k for k,v in TYPES.items()};self.nodes=MappingProxyType({n:(kinds[types[n]],locations[n]) for n in range(len(types))});self.edges=NativeEdges(compact)
 def validate(self,path,digest):
  if Path(path)!=self.path or digest!=self.digest or sha(self.path)!=digest:raise ValueError('graph identity changed')
