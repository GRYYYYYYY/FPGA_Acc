"""Read-only Python RR snapshot; fresh file authentication on every reuse."""
from dataclasses import dataclass
from types import MappingProxyType
from pathlib import Path
import json
from class_cached_rc_endpoint_context_v1 import load_endpoints
from pre_route_endpoints import sha
@dataclass(frozen=True)
class Node:
 attrs:object
 children:object
 def get(self,key,default=None):return self.attrs.get(key,default)
 def find(self,key):return self.children.get(key)
def freeze_node(node):
 return Node(MappingProxyType(dict(node.attrib)),MappingProxyType({child.tag:freeze_node(child) for child in node}))
@dataclass(frozen=True)
class FrozenIntegerRC:
 fields:object
 scale:int
 increments:tuple
 initials:tuple
 electrical:tuple
 def node(self,n):
  if type(n) is not int or not 0<=n<len(self.initials):raise ValueError('invalid node')
  return self.electrical[n]
 def initial(self,n):self.node(n);return self.initials[n]
 def increment(self,i):return self.increments[i]
 def path(self,source,sink,edges):
  delay=self.initial(source);self.node(sink);node=source;seen={node};f=self.fields
  for eid in edges:
   matches=[i for i in range(f['row_offsets'][node],f['row_offsets'][node+1]) if f['edge_ids'][i]==eid]
   if len(matches)!=1:raise ValueError('absent or ambiguous edge')
   i=matches[0];node=f['dest_ranks'][i]
   if node in seen:raise ValueError('cyclic path')
   seen.add(node);delay+=self.increments[i]
  if node!=sink:raise ValueError('wrong sink')
  return delay
@dataclass(frozen=True)
class ImmutableEndpointContext:
 graph:Path
 digest:str
 nodes:tuple
 fields:object
 rc:FrozenIntegerRC
 @classmethod
 def build(cls,endpoint):
  g,d,n,f,rc,_=load_endpoints(endpoint);fields=MappingProxyType({k:tuple(v) for k,v in f.items()})
  frozen=FrozenIntegerRC(fields,rc.scale,tuple(rc.increments),tuple(rc.initial(i) for i in range(len(n))),tuple(rc.node(i) for i in range(len(n))))
  return cls(g.resolve(),d,tuple(freeze_node(node) for node in n),fields,frozen)
 def load(self,endpoint):
  meta=json.loads(Path(endpoint).read_text())
  if not all(sha(v['path'])==v['sha256'] for v in meta['inputs'].values()):raise ValueError('endpoint input changed')
  if Path(meta['inputs']['graph']['path']).resolve()!=self.graph or meta['graph_sha256']!=self.digest:raise ValueError('graph epoch mismatch')
  return self.graph,self.digest,self.nodes,self.fields,self.rc,meta['connections']
