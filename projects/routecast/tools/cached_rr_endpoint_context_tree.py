"""Synchronous three-entry immutable RR build cache; authenticate every binding."""
import json
from pathlib import Path
from types import MappingProxyType
from dataclasses import dataclass
from collections import OrderedDict
from pre_route_endpoints import sha
from nonzero_rc_endpoint_context_memo_tree import load_endpoints as build
from csr_exact_buffered_rc import ExactBufferedRC
from integer_rc_context_class_memo import IntegerRC

@dataclass(frozen=True)
class FrozenNode:
 tag:str
 attrib:object
 children:tuple
 def get(self,key,default=None):return self.attrib.get(key,default)
 def find(self,path):
  current=self
  for tag in path.split('/'):
   current=next((x for x in current.children if x.tag==tag),None)
   if current is None:return None
  return current

def freeze_node(node):return FrozenNode(node.tag,MappingProxyType(dict(node.attrib)),tuple(freeze_node(x) for x in node))

@dataclass(frozen=True)
class FrozenElectrical:
 fields:object
 node_classes:object
 classes:tuple
 switches:object
 cache:object
 node=ExactBufferedRC.node
 increment=ExactBufferedRC.increment
 path=ExactBufferedRC.path

@dataclass(frozen=True)
class FrozenInteger:
 rc:object
 fields:object
 scale:int
 increments:object
 node=IntegerRC.node
 initial=IntegerRC.initial
 increment=IntegerRC.increment
 encode=IntegerRC.encode
 path=IntegerRC.path

def readonly(values):
 from array import array
 return memoryview(array('Q',values).tobytes()).cast('Q').toreadonly()
_CACHE=OrderedDict();STATS={'builds':0,'hits':0,'evictions':0}
def clear_cache():
 _CACHE.clear()
 for key in STATS:STATS[key]=0

def load_endpoints(endpoint_path):
 endpoint=json.loads(Path(endpoint_path).read_text())
 for value in endpoint['inputs'].values():
  if sha(value['path'])!=value['sha256']:raise ValueError('changed endpoint input')
 graph=Path(endpoint['inputs']['graph']['path']);digest=sha(graph)
 if digest!=endpoint['graph_sha256']:raise ValueError('changed graph binding')
 key=(str(graph.resolve()),digest)
 if key in _CACHE:
  snapshot=_CACHE[key];_CACHE.move_to_end(key);STATS['hits']+=1
 else:
  context=build(endpoint_path);assert context[1]==digest
  fields=MappingProxyType({name:readonly(values) for name,values in context[3].items()});raw=context[4];electrical=raw.rc
  rc=FrozenElectrical(fields,readonly(electrical.node_classes),tuple(tuple(x) for x in electrical.classes),MappingProxyType(dict(electrical.switches)),MappingProxyType(dict(electrical.cache)))
  integer=FrozenInteger(rc,fields,raw.scale,readonly(raw.increments));nodes=tuple(freeze_node(x) for x in context[2]);snapshot=(nodes,fields,integer)
  if sha(graph)!=digest:raise ValueError('graph changed during cache build')
  _CACHE[key]=snapshot;STATS['builds']+=1
  if len(_CACHE)>3:_CACHE.popitem(last=False);STATS['evictions']+=1
 nodes,fields,integer=snapshot
 return graph,digest,nodes,fields,integer,endpoint['connections']
