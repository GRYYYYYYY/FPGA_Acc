"""One immutable graph context, independent admitted source states and COW branches.

Geometry validation is shared. Each initial source still checks every ordered
path, graph edge, NET source and parent relation. Branches reuse only an already
published state from this cache implementation; they do not import raw counters.
State ownership is per cache instance, not a globally unique generation number.
"""
from collections import Counter,defaultdict
from dataclasses import dataclass
from types import MappingProxyType
from retained_tree_frontier_state_v2 import Cache as PathCache
from retained_tree_frontier_state_v1 import EXPAND,Record,State
from incremental_IPIN_feature_cache_v1 import pages

@dataclass(frozen=True,init=False)
class GraphContext:
 epoch: str
 geometry: object
 edge_exists: object
 def __init__(self,epoch,geometry,edge_exists):
  if not isinstance(epoch,str) or not epoch:raise ValueError('graph epoch')
  if not callable(edge_exists):raise ValueError('edge checker required')
  geo={}
  for node,value in geometry.items():
   if type(node) is not int or node<0 or not isinstance(value,(list,tuple)) or len(value)!=6:raise ValueError('geometry schema')
   kind,x0,x1,y0,y1,layer=value
   if kind not in EXPAND|{'IPIN','SINK'} or any(type(n) is not int or n<0 for n in value[1:]) or x0>x1 or y0>y1:raise ValueError('node rectangle')
   geo[node]=tuple(value)
  object.__setattr__(self,'epoch',epoch);object.__setattr__(self,'geometry',MappingProxyType(geo));object.__setattr__(self,'edge_exists',edge_exists)

class Cache(PathCache):
 def __init__(self,context,records):
  if type(context) is not GraphContext:raise ValueError('validated graph context required')
  self._context=context;self._epoch=context.epoch;self._geometry=context.geometry;self._edge_exists=context.edge_exists;queries={};by_net=defaultdict(list);parents=defaultdict(dict)
  for row in records:
   if set(row)!={'connection_id','net_id','source','sink','path'}:raise ValueError('record schema')
   cid,net,src,sink=[row[k] for k in ['connection_id','net_id','source','sink']]
   if any(type(k) is not int or k<0 for k in [cid,net,src,sink]) or cid in queries:raise ValueError('identity')
   self._endpoint(src,'SOURCE');self._endpoint(sink,'SINK')
   if not isinstance(row['path'],(list,tuple)):raise ValueError('ordered path schema')
   path=tuple(row['path'])
   if len(path)<2 or path[0]!=src or path[-1]!=sink or any(type(n) is not int or n not in self._geometry for n in path) or len(set(path))!=len(path):raise ValueError('ordered path endpoints/cycle')
   if any(self._geometry[n][0] in ['SOURCE','SINK'] for n in path[1:-1]):raise ValueError('internal endpoint')
   for a,b in zip(path,path[1:]):
    if not self._edge_exists(a,b):raise ValueError('path RR edge')
    if b in parents[net] and parents[net][b]!=a:raise ValueError('NET multiple parents')
    parents[net][b]=a
   queries[cid]=Record(net,src,sink,path);by_net[net].append(cid)
  nets={}
  for net,cids in by_net.items():
   sources={queries[c].source for c in cids}
   if len(sources)!=1:raise ValueError('NET source mismatch')
   refs=Counter(n for c in cids for n in queries[c].path);nets[net]=self._net(next(iter(sources)),frozenset(cids),refs)
  self._state=State(0,pages(queries),pages(nets));self._pending={}
 def branch(self,graph_epoch,generation):
  if graph_epoch!=self._epoch or type(generation) is not int or generation!=self.generation:raise ValueError('graph/generation mismatch')
  result=object.__new__(type(self));result._context=self._context;result._epoch=self._epoch;result._geometry=self._geometry;result._edge_exists=self._edge_exists;result._state=self._state;result._pending={};return result
