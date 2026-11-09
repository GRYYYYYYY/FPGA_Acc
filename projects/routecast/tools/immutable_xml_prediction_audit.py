"""Reuse compact immutable original-XML topology; reauthenticate each audit."""
from array import array
from types import SimpleNamespace
import xml.etree.ElementTree as ET
from prepared_csr import TYPES
from pre_route_endpoints import sha
from streaming_prediction_audit import Nodes
from physical_prediction_audit import audit
from net_union_topology import diagnose

class CompactEdges:
 def __init__(self,source,destination,switch):
  self.source=memoryview(source.tobytes()).cast('Q');self.destination=memoryview(destination.tobytes()).cast('Q');self.switch=memoryview(switch.tobytes()).cast('Q')
 def __len__(self):return len(self.source)
 def __getitem__(self,n):
  if type(n) is not int or not 0<=n<len(self):raise KeyError(n)
  return SimpleNamespace(source=self.source[n],sink=self.destination[n],switch_id=self.switch[n])

class ImmutableXMLAudit:
 def __init__(self,path,expected_sha256):
  self.path=path;before=sha(path)
  if before!=expected_sha256:raise ValueError('unexpected graph digest')
  types=array('B');caps=array('Q');spans=array('Q');sources=array('Q');dest=array('Q');switch=array('Q');stack=[]
  for event,e in ET.iterparse(path,events=('start','end')):
   if event=='start':
    stack.append(e)
    if len(stack)==1 and e.tag!='rr_graph':raise ValueError('expected RR root')
    continue
   parent=stack[-2].tag if len(stack)>1 else None
   if e.tag=='node' and parent=='rr_nodes':
    if int(e.get('id'))!=len(types):raise ValueError('contiguous ascending node IDs required')
    kind=e.get('type');capacity=int(e.get('capacity'));loc=e.find('loc')
    if capacity<0 or kind not in TYPES:raise ValueError('invalid node')
    types.append(TYPES[kind]);caps.append(capacity);spans.append(max(int(loc.get('xhigh'))-int(loc.get('xlow')),int(loc.get('yhigh'))-int(loc.get('ylow')))+1)
   elif e.tag=='edge' and parent=='rr_edges':
    sources.append(int(e.get('src_node')));dest.append(int(e.get('sink_node')));switch.append(int(e.get('switch_id')))
   if (e.tag,parent) in (('node','rr_nodes'),('edge','rr_edges'),('switch','switches'),('segment','segments')):stack[-2].remove(e);e.clear()
   stack.pop()
  if any(n>=len(types) for n in sources) or any(n>=len(types) for n in dest):raise ValueError('invalid arc node')
  if sha(path)!=before:raise ValueError('graph changed during load')
  self.digest=before;self.types=memoryview(types.tobytes());self.caps=memoryview(caps.tobytes()).cast('Q');self.spans=memoryview(spans.tobytes()).cast('Q')
  self.graph=SimpleNamespace(nodes=Nodes(self.types,self.caps),edges=CompactEdges(sources,dest,switch),sha256=before)
  self.payload_bytes=len(types)+8*(len(caps)+len(spans)+len(sources)+len(dest)+len(switch))
 def verify(self,endpoints,prediction,topology=False):
  if sha(self.path)!=self.digest:raise ValueError('graph changed before audit')
  wanted=set()
  for row in prediction['connections']:
   for eid in row['physical_edge_ids'] or ():
    if type(eid) is not int or not 0<=eid<len(self.graph.edges):raise ValueError('unknown physical edge')
    wanted.add(eid)
  checked=audit(self.graph,endpoints,prediction);overuse=span=all_overuse=0
  for key,used in prediction['node_occupancy'].items():
   n=int(key)
   if used and not self.caps[n]:raise ValueError('disabled resource occupied')
   all_overuse+=max(0,used-self.caps[n])
   if self.types[n] in (TYPES['CHANX'],TYPES['CHANY']):span+=used*self.spans[n];overuse+=max(0,used-self.caps[n])
  if sha(self.path)!=self.digest:raise ValueError('graph changed during audit')
  structural={}
  if topology:structural['net_union_topology']=diagnose(self.graph,prediction) if checked['completed']==checked['requested'] else {'status':'not_evaluated_incomplete_paths'}
  return {**structural,**checked,'original_xml_edges':len(self.graph.edges),'selected_edges':len(wanted),'channel_net_span_sum':span,'predicted_channel_overuse_units':overuse,'all_type_overuse_units':all_overuse,'scope':'original XML individual paths and unique-net occupancy; no joint tree/pin legality or native QoR'}
