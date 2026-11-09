"""Memory-mapped native MAP endpoint table, explicit graph/frame/CID domains."""
import json,hashlib,mmap,struct,math,xml.etree.ElementTree as ET
from pathlib import Path
from bound_native_map_query_v1 import f32,frombits

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
class Query:
 def __init__(self,path,endpoint,timing,payload_sha256):
  self.file=Path(path).open('rb');self.data=None
  try:self._load(endpoint,timing,payload_sha256)
  except BaseException:self.close();raise
 def _load(self,endpoint,timing,payload_sha256):
  meta=json.loads(Path(endpoint).read_text());self.graph_sha256=meta['graph_sha256'];self.endpoint_sha256=sha(endpoint);graph=Path(meta['inputs']['graph']['path']);
  if sha(graph)!=self.graph_sha256:raise ValueError('graph content')
  head=self.file.readline().decode('ascii').split()
  if len(head)!=7 or head[:2]!=['ALLMAP','1'] or head[2:4]!=[self.graph_sha256,self.endpoint_sha256]:raise ValueError('allMAP graph/frame header')
  self.n,nt,np=map(int,head[4:]);pins={};targets=[]
  if min(self.n,nt,np)<=0 or nt>self.n:raise ValueError('header counts')
  for _ in range(np):
   w=self.file.readline().decode('ascii').split()
   if len(w)!=5 or w[0]!='P':raise ValueError('pin record')
   net,pin,source,target=map(int,w[1:]);key=net,pin
   if net<0 or pin<=0 or key in pins or not(0<=source<self.n and 0<=target<self.n):raise ValueError('duplicate/invalid pin')
   pins[key]=(source,target)
  for _ in range(nt):
   w=self.file.readline().decode('ascii').split()
   if len(w)!=2 or w[0]!='T':raise ValueError('target record')
   targets.append(int(w[1]))
  if targets!=sorted(set(targets)) or set(targets)!={t for s,t in pins.values()} or self.file.readline()!=b'DATA\n':raise ValueError('target list/domain')
  self.offset=self.file.tell();self.data=mmap.mmap(self.file.fileno(),0,access=mmap.ACCESS_READ)
  if len(self.data)!=self.offset+self.n*nt*8:raise ValueError('partial/trailing payload')
  view=memoryview(self.data)[self.offset:];digest=hashlib.sha256(view).hexdigest();del view
  if digest!=payload_sha256:raise ValueError('payload SHA')
  self.targets={t:i for i,t in enumerate(targets)};root=ET.parse(graph).getroot();nodes=list(root.find('rr_nodes'));self.kinds=[x.get('type') for x in nodes]
  if len(nodes)!=self.n or any(int(n.get('id'))!=i for i,n in enumerate(nodes)):raise ValueError('node count/order')
  if any(not 0<=s<self.n or not 0<=t<self.n or self.kinds[s]!='SOURCE' or self.kinds[t]!='SINK' for s,t in pins.values()):raise ValueError('pin node types')
  self.exits={}
  for e in root.find('rr_edges'):
   u,v=int(e.get('src_node')),int(e.get('sink_node'))
   if self.kinds[v]=='SOURCE' or self.kinds[v]=='OPIN' and self.kinds[u]!='SOURCE':raise ValueError('graph grammar')
   if self.kinds[u]=='SOURCE':
    if self.kinds[v]!='OPIN':raise ValueError('source exit')
    self.exits.setdefault(u,set()).add(v)
  endpoint_rows={x['connection_id']:x for x in meta['connections']};self.connections={}
  for t in json.loads(Path(timing).read_text()):
   if t.get('ignored') or 'connection_id' not in t:continue
   cid=t['connection_id'];e=endpoint_rows[cid];s,target=pins[t['native_net_id'],t['local_sink_pin']]
   if (e['source'],e['sink'],e['full_connection_id'])!=(s,target,t['full_connection_id']) or (s,target)!=(t['source_rr'],t['target_rr']):raise ValueError('CID/pin mismatch')
   if cid in self.connections:raise ValueError('duplicate CID')
   self.connections[cid]=(s,target)
  if set(self.connections)!=set(endpoint_rows):raise ValueError('partial endpoint coverage')
  self.extra_native_pins=np-len(self.connections)
 def query(self,node,cid,criticality_bits,*,graph_sha256,endpoint_sha256,upstream_bits='00000000'):
  if self.data is None:raise ValueError('closed query')
  if graph_sha256!=self.graph_sha256 or endpoint_sha256!=self.endpoint_sha256:raise ValueError('stale graph/frame')
  if type(cid) is not int or type(node) is not int or cid not in self.connections or not 0<=node<self.n:raise ValueError('unsupported CID/node')
  source,target=self.connections[cid]
  if self.kinds[node] not in ['CHANX','CHANY','IPIN','SINK'] and node!=source and node not in self.exits.get(source,set()):raise ValueError('unsupported perNET node')
  c=frombits(criticality_bits)
  if not math.isfinite(c) or not 0<=c<=1 or frombits(upstream_bits)!=0:raise ValueError('criticality/Rup')
  zero,one=struct.unpack_from('<ff',self.data,self.offset+(self.targets[target]*self.n+node)*8)
  if not all(math.isfinite(x) and x>=0 for x in [zero,one]):raise ValueError('nonfinite/negative native lookup')
  if self.kinds[node] in ['IPIN','SINK']:
   if zero!=one:raise ValueError('terminal branch')
   return zero
  return f32(f32(c*one)+f32(f32(1-c)*zero))
 def close(self):
  if self.data is not None:self.data.close();self.data=None
  self.file.close()
