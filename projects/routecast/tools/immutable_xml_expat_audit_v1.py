"""Independent streaming topology reader; original full verify body inherited unchanged."""
from array import array
from types import SimpleNamespace
from xml.parsers import expat
from pre_route_endpoints import sha
from prepared_csr import TYPES
from streaming_prediction_audit import Nodes
from immutable_xml_prediction_audit import ImmutableXMLAudit,CompactEdges

class ImmutableExpatAudit(ImmutableXMLAudit):
 def __init__(self,path,expected_sha256):
  self.path=path;before=sha(path)
  if before!=expected_sha256:raise ValueError('unexpected graph digest')
  types=array('B');caps=array('Q');spans=array('Q');sources=array('Q');dest=array('Q');switch=array('Q');stack=[]
  def start(tag,attrs):
   parent=stack[-1][0] if stack else None
   if not stack and tag!='rr_graph':raise ValueError('expected RR root')
   if tag=='loc' and parent=='node' and stack[-1][2] is None:stack[-1][2]=attrs
   stack.append([tag,attrs if (tag,parent) in [('node','rr_nodes'),('edge','rr_edges')] else None,None])
  def end(tag):
   frame=stack.pop();assert frame[0]==tag;parent=stack[-1][0] if stack else None;attrs=frame[1]
   if tag=='node' and parent=='rr_nodes':
    if int(attrs.get('id'))!=len(types):raise ValueError('contiguous ascending node IDs required')
    kind=attrs.get('type');capacity=int(attrs.get('capacity'));loc=frame[2]
    if capacity<0 or kind not in TYPES:raise ValueError('invalid node')
    types.append(TYPES[kind]);caps.append(capacity);spans.append(max(int(loc.get('xhigh'))-int(loc.get('xlow')),int(loc.get('yhigh'))-int(loc.get('ylow')))+1)
   elif tag=='edge' and parent=='rr_edges':
    sources.append(int(attrs.get('src_node')));dest.append(int(attrs.get('sink_node')));switch.append(int(attrs.get('switch_id')))
  parser=expat.ParserCreate();parser.StartElementHandler=start;parser.EndElementHandler=end
  with open(path,'rb') as f:
   while True:
    chunk=f.read(1<<20)
    if not chunk:break
    parser.Parse(chunk,False)
  parser.Parse(b'',True);assert not stack
  if any(n>=len(types) for n in sources) or any(n>=len(types) for n in dest):raise ValueError('invalid arc node')
  if sha(path)!=before:raise ValueError('graph changed during load')
  self.digest=before;self.types=memoryview(types.tobytes());self.caps=memoryview(caps.tobytes()).cast('Q');self.spans=memoryview(spans.tobytes()).cast('Q')
  self.graph=SimpleNamespace(nodes=Nodes(self.types,self.caps),edges=CompactEdges(sources,dest,switch),sha256=before)
  self.payload_bytes=len(types)+8*(len(caps)+len(spans)+len(sources)+len(dest)+len(switch))
