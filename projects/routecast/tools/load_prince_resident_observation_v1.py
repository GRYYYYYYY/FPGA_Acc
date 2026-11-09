"""Read-only coherent phase/identity consumer; no native mutation or restore."""
import json,hashlib,struct,math,xml.etree.ElementTree as ET
from pathlib import Path
from types import MappingProxyType
PHASE='post_route_accumulated_cost_and_timing_update__pre_dynamic_BB_update_and_pres_advance'
def fail(ok,message):
 if not ok:raise ValueError(message)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def word(x):return struct.unpack('<f',struct.pack('<I',x))[0]
class Consumer:
 def __init__(self):self._files={};self._graphs={}
 def _read(self,path,h):
  p=Path(path);s=p.stat();tag=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns);cached=self._files.get(str(p))
  if cached and cached[0]==tag and cached[1]==h:return cached[2]
  raw=p.read_bytes();after=p.stat();fail(tag==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'file changed during read');fail(digest(raw)==h,'binding drift');self._files[str(p)]=(tag,h,raw);return raw
 def load(self,path,expected):
  manifest=json.loads(Path(path).read_text());fail(manifest.get('schema')=='ROUTECAST_RESIDENT_NATIVE_OBSERVATION_V1','schema');identity=manifest['identity'];fail(identity==expected and set(identity)=={'case','graph_sha256','netlist_sha256','placement_sha256','binary_sha256','phase','iteration'},'identity mismatch');fail(type(identity['iteration']) is int and identity['iteration']>0 and identity['phase']==PHASE,'phase/iteration');paths=manifest['paths'];bindings=manifest['bindings']
  for name,key in [('graph','graph_sha256'),('netlist','netlist_sha256'),('placement','placement_sha256'),('binary','binary_sha256')]:fail(bindings.get(paths[name])==identity[key],'identity binding mismatch')
  for p,h in bindings.items():self._read(p,h)
  def read(name):return self._read(paths[name],bindings[paths[name]])
  gh=identity['graph_sha256']
  if gh not in self._graphs:
   graph=ET.fromstring(read('graph'));kinds={'SOURCE':0,'SINK':1,'IPIN':2,'OPIN':3,'CHANX':4,'CHANY':5};nodes=[]
   for n in graph.findall('rr_nodes/node'):fail(int(n.get('id'))==len(nodes),'graph order');nodes.append((kinds[n.get('type')],int(n.get('capacity'))))
   grid=graph.findall('grid/grid_loc');limits=tuple(max(int(x.get(k,'0')) for x in grid) for k in ['x','y','layer']);self._graphs[gh]=(tuple(nodes),limits)
  nodes,limits=self._graphs[gh];raw=read('RR');fail(len(raw)>=24 and raw[:8]==b'RCBND001','RR header');iteration,n=struct.unpack_from('<QQ',raw,8);fail(iteration==identity['iteration'] and n==manifest['node_count']==len(nodes) and len(raw)==24+24*n,'RR epoch/shape');records=[]
  for idx,(nid,kind,occ,cap,bits) in enumerate(struct.iter_unpack('<QIiiI',raw[24:])):
   fail(nid==idx and (kind,cap)==nodes[idx] and occ>=0 and math.isfinite(word(bits)) and word(bits)>=1,'RR domain');records.append((kind,occ,cap,bits))
  mapping=json.loads(read('NET_mapping'));proofs=[p for p in bindings if p.endswith('/NET_mapping_verification.json')];fail(len(proofs)==1,'mapping proof missing');proof=json.loads(self._read(proofs[0],bindings[proofs[0]]));fail(proof['mapping']==paths['NET_mapping'] and proof['bindings'].get(paths['NET_mapping'])==bindings[paths['NET_mapping']],'mapping proof binding')
  for p,h in proof['bindings'].items():self._read(p,h)
  fail(len(mapping)==manifest['NET_count'] and {x['native_NET_id'] for x in mapping}==set(range(len(mapping))) and len({x['endpoint_NET_id'] for x in mapping})==len(mapping) and len({x['name'] for x in mapping})==len(mapping),'mapping bijection');mapping=sorted(mapping,key=lambda x:x['native_NET_id']);fail(all(type(x['ignored_global']) is bool for x in mapping),'mapping role')
  raw=read('boxes');fail(len(raw)>=24 and raw[:8]==b'RCBOX001','BB header');ii,count=struct.unpack_from('<QQ',raw,8);fail(ii==iteration and count==len(mapping) and len(raw)==24+32*count,'BB epoch/shape');boxes={}
  for idx,(native,xmin,xmax,ymin,ymax,lmin,lmax) in enumerate(struct.iter_unpack('<Q6i',raw[24:])):
   fail(native==idx and 0<=xmin<=xmax<=limits[0] and 0<=ymin<=ymax<=limits[1] and 0<=lmin<=lmax<=limits[2],'BB domain');boxes[mapping[idx]['endpoint_NET_id']]=(native,xmin,xmax,ymin,ymax,lmin,lmax)
  phase=[list(map(int,line.split())) for line in read('phase').decode().splitlines()];fail([p[0] for p in phase]==list(range(1,len(phase)+1)) and iteration<=len(phase),'phase coverage');t=phase[iteration-1];fail(t==manifest['phase_row'] and len(t)==10 and t[0]==iteration,'phase row');fail(math.isfinite(word(t[1])) and word(t[1])>=0,'pres domain');over=[max(0,row[1]-row[2]) for row in records];fail(t[2:5]==[sum(x>0 for x in over),sum(over),max(over,default=0)],'overuse summary');fail(all(math.isfinite(word(bits)) for bits in t[6:]),'timing summary');fail(manifest['units']==dict(timing='seconds',RR_cost='native_float32',pres_fac='native_float32'),'units')
  return MappingProxyType(dict(identity=MappingProxyType(dict(identity)),RR=tuple(records),boxes=MappingProxyType(boxes),NET_mapping=tuple((x['native_NET_id'],x['endpoint_NET_id'],x['name'],x['ignored_global']) for x in mapping),pres_fac_bits=t[1],timing_summary_bits=tuple(t[6:]),overuse_units=t[3]))
