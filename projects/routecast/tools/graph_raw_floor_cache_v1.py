"""Exact graph/objective-affine raw floors; callers must supply verified witnesses."""
from dataclasses import dataclass
VERSION='XML_ZERO_RC_SWITCH_TDEL_POSITIVE_CAPACITY_SCALE1E18_V1'
@dataclass(frozen=True)
class Entry:
 minimum: object
 edges: object
 origin: str
class Cache:
 def __init__(self):self._entries={}
 def key(self,graph,source,sink,objective=VERSION):
  if not isinstance(graph,str) or len(graph)!=64 or any(c not in '0123456789abcdef' for c in graph):raise ValueError('invalid graph hash')
  if any(type(n) is not int or n<0 for n in (source,sink)):raise ValueError('invalid RR endpoint')
  if objective!=VERSION:raise ValueError('unsupported raw floor objective')
  return graph,source,sink,objective
 def get(self,graph,source,sink,objective=VERSION):return self._entries.get(self.key(graph,source,sink,objective))
 def put(self,graph,source,sink,minimum,edges,origin,objective=VERSION):
  key=self.key(graph,source,sink,objective)
  if not isinstance(origin,str) or not origin:raise ValueError('missing verified origin')
  if minimum is None:
   if edges is not None:raise ValueError('unreachable witness mismatch')
  else:
   if type(minimum) is not int or not 0<=minimum<2**64-1 or edges is None:raise ValueError('invalid raw floor')
   edges=tuple(edges)
   if any(type(e) is not int or e<0 for e in edges):raise ValueError('invalid physical edge')
  previous=self._entries.get(key)
  if previous is not None:
   if previous.minimum!=minimum:raise ValueError('conflicting verified minima')
   return previous # First admitted witness retained for equal-cost alternatives.
  entry=Entry(minimum,edges,origin);self._entries[key]=entry;return entry
 def __len__(self):return len(self._entries)
