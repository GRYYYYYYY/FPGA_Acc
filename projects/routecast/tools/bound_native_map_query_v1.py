"""Bounded native endpoint-table adapter, exact f32 algebra, explicit rejections."""
import hashlib,json,struct,math,xml.etree.ElementTree as ET
from pathlib import Path

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def f32(x):return struct.unpack('f',struct.pack('f',x))[0]
def frombits(x):
 if len(x)!=8:raise ValueError('float bits width')
 return struct.unpack('>f',bytes.fromhex(x))[0]
class Query:
 def __init__(self,path,endpoint,timing):
  path,endpoint=Path(path),Path(endpoint);meta=json.loads(endpoint.read_text());self.endpoint_sha256=sha(endpoint);self.graph_sha256=meta['graph_sha256'];graph=Path(meta['inputs']['graph']['path'])
  if sha(graph)!=self.graph_sha256:raise ValueError('graph content')
  queries={q['connection_id']:q for q in meta['connections']};pinmeta=[q for q in json.loads(Path(timing).read_text()) if q['native_net_id']==0];self.targets={};sources=set()
  for q in pinmeta:
   e=queries[q['connection_id']]
   if (e['source'],e['sink'],e['full_connection_id'])!=(q['source_rr'],q['target_rr'],q['full_connection_id']):raise ValueError('timing/endpoint identity')
   self.targets[q['local_sink_pin']]=e['sink'];sources.add(e['source'])
  if set(self.targets)!={1,2} or len(sources)!=1:raise ValueError('fixed NET0 domain')
  source=next(iter(sources));self.kinds=[];outgoing={}
  for _,e in ET.iterparse(graph):
   if e.tag=='node' and e.get('capacity') is not None:
    if int(e.get('id'))!=len(self.kinds):raise ValueError('node order')
    self.kinds.append(e.get('type'))
   elif e.tag=='edge':outgoing.setdefault(int(e.get('src_node')),set()).add(int(e.get('sink_node')))
  for u,vs in outgoing.items():
   if any(self.kinds[v]=='SOURCE' or self.kinds[v]=='OPIN' and self.kinds[u]!='SOURCE' for v in vs):raise ValueError('graph grammar')
  if any(self.kinds[n]!='OPIN' for n in outgoing.get(source,set())):raise ValueError('source exit')
  self.allowed={n for n,k in enumerate(self.kinds) if k in ['CHANX','CHANY','IPIN','SINK']}|{source}|outgoing.get(source,set());self.values={};seen_targets={}
  with path.open() as f:
   h=next(f).split()
   if h!=['MAP_QUERY','1',self.graph_sha256,self.endpoint_sha256,str(len(self.kinds)),str(len(self.allowed)),str(source)]:raise ValueError('probe graph/frame header')
   for line in f:
    w=line.split()
    if w[0]=='T':
     pin,target=map(int,w[1:]);
     if pin in seen_targets:raise ValueError('duplicate target')
     seen_targets[pin]=target;continue
    if len(w)!=6 or w[0]!='Q':raise ValueError('query record')
    pin,node,target=map(int,w[1:4]);key=pin,node
    if pin not in self.targets or node not in self.allowed or target!=self.targets[pin] or key in self.values:raise ValueError('query domain/duplicate')
    self.values[key]=(frombits(w[4]),frombits(w[5]))
  if seen_targets!=self.targets or set(self.values)!={(pin,n) for pin in self.targets for n in self.allowed}:raise ValueError('partial matrix')
 def query(self,node,pin,criticality_bits,*,graph_sha256,endpoint_sha256,upstream_bits='00000000'):
  if graph_sha256!=self.graph_sha256 or endpoint_sha256!=self.endpoint_sha256:raise ValueError('stale graph/frame')
  if node not in self.allowed or pin not in self.targets:raise ValueError('unsupported node/pin')
  c=frombits(criticality_bits);up=frombits(upstream_bits)
  if not math.isfinite(c) or not 0<=c<=1 or up!=0:raise ValueError('criticality/upstream')
  zero,one=self.values[pin,node]
  if not all(math.isfinite(x) and x>=0 for x in [zero,one]):raise ValueError('native nonfinite/negative endpoint cost')
  if self.kinds[node] in ['IPIN','SINK']:
   if zero!=one:raise ValueError('terminal branch mismatch')
   return zero
  return f32(f32(c*one)+f32(f32(1-c)*zero))
