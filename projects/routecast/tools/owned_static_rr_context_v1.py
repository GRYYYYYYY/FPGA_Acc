"""Process-owned immutable graph/RC cache; current queries and every input digest re-read."""
import json
from pathlib import Path
from types import MappingProxyType
from class_cached_rc_endpoint_context_v1 import load_endpoints as original_load
from pre_route_endpoints import sha
_cache={};_loads=0;_accesses=0
class FrozenElement:
 __slots__=('tag','attrib','text','tail','children','_sealed')
 def __init__(self,element):
  object.__setattr__(self,'tag',element.tag);object.__setattr__(self,'attrib',MappingProxyType(dict(element.attrib)));object.__setattr__(self,'text',element.text);object.__setattr__(self,'tail',element.tail);object.__setattr__(self,'children',tuple(FrozenElement(x) for x in element));object.__setattr__(self,'_sealed',True)
 def __setattr__(self,name,value):raise TypeError('immutable original graph element')
 def get(self,name,default=None):return self.attrib.get(name,default)
 def __iter__(self):return iter(self.children)
 def find(self,tag):
  if any(x in tag for x in '/[]*'):raise ValueError('only direct original child lookup supported')
  return next((x for x in self.children if x.tag==tag),None)
 def findall(self,tag):
  if any(x in tag for x in '/[]*'):raise ValueError('only direct original child lookup supported')
  return [x for x in self.children if x.tag==tag]
def load_endpoints(path):
 global _loads,_accesses
 path=Path(path).resolve();ep=json.loads(path.read_text());assert all(sha(x['path'])==x['sha256'] for x in ep['inputs'].values());graph=Path(ep['inputs']['graph']['path']).resolve();digest=sha(graph);assert digest==ep['graph_sha256'];key=(str(graph),digest);_accesses+=1
 if key not in _cache:
  g,h,nodes,f,rc,_=original_load(path);assert Path(g).resolve()==graph and h==digest
  fields=MappingProxyType({k:memoryview(v.tobytes()).cast('Q') for k,v in f.items()});frozen=tuple(FrozenElement(x) for x in nodes);rc.fields=fields;rc.rc.fields=fields;rc.increments=tuple(rc.increments);rc.initial_by_class=MappingProxyType(dict(rc.initial_by_class));rc.rc.node_classes=tuple(rc.rc.node_classes);rc.rc.classes=tuple(rc.rc.classes);rc.rc.switches=MappingProxyType(dict(rc.rc.switches));assert sha(graph)==digest
  _cache.clear();_cache[key]=(graph,digest,frozen,fields,rc);_loads+=1
 assert sha(graph)==digest;context=_cache[key]
 # No paths, floors, prices, epochs, endpoint lists, predictions or labels retained.
 return (*context,ep['connections'])
def diagnostics():return dict(contexts=len(_cache),loads=_loads,accesses=_accesses,scope='Only one owned immutable RR/RC context; full current input digests and queries refreshed on every access. All dynamic model work remains required.')
