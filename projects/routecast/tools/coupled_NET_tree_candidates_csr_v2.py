"""Owned validated physical CSR index reused across complete NET tree admissions."""
from array import array
from bisect import bisect_right
from collections.abc import Mapping
from coupled_NET_tree_candidates_v1 import select

class _ArrayMapping(Mapping):
 def __init__(self,values):self._values=values
 def __getitem__(self,key):
  if type(key) is not int or not 0<=key<len(self._values):raise KeyError(key)
  return self._values[key]
 def __len__(self):return len(self._values)
 def __iter__(self):return iter(range(len(self._values)))

class CSRIndex:
 """Copy CSR storage once; expose only readonly views and indexed arcs.

Physical edge ID is its CSR slot. Source derived by upper_bound offsets,
including duplicate offsets for nodes with no outgoing edges.
 """
 def __init__(self,offsets,destination,costs,capacities,kinds):
  try:
   self._offsets=memoryview(array('Q',offsets)).toreadonly()
   self._destination=memoryview(array('I',destination)).toreadonly()
   self._costs=memoryview(array('Q',costs)).toreadonly()
   cv=memoryview(array('I',capacities)).toreadonly()
  except (OverflowError,TypeError,ValueError) as e:raise ValueError('invalid unsigned CSR storage') from e
  kv=tuple(kinds);n=len(cv);m=len(self._destination)
  if len(self._offsets)!=n+1 or not n or self._offsets[0]!=0 or self._offsets[-1]!=m or len(self._costs)!=m or len(kv)!=n:raise ValueError('CSR shape')
  if any(a>b for a,b in zip(self._offsets,self._offsets[1:])) or any(v>=n for v in self._destination):raise ValueError('CSR bounds/order')
  if any(k not in ['SOURCE','SINK','IPIN','OPIN','CHANX','CHANY'] for k in kv):raise ValueError('RR node kind')
  self.capacities=_ArrayMapping(cv);self.kinds=_ArrayMapping(kv);self.node_count=n;self.edge_count=m
 def arc(self,eid):
  if type(eid) is not int or not 0<=eid<self.edge_count:raise ValueError('unknown physical edge')
  return bisect_right(self._offsets,eid)-1,self._destination[eid],self._costs[eid]

def tree_candidate(index,source,sink_paths,floors,budgets):
 if not isinstance(index,CSRIndex):raise ValueError('validated CSR index required')
 capacities=index.capacities;kinds=index.kinds
 if set(sink_paths)!=set(floors) or set(floors)!=set(budgets) or not sink_paths:
  raise ValueError('sink/floor/budget domain')
 if kinds.get(source)!='SOURCE':raise ValueError('source kind')
 nodes={source};parents={};used=set();costs={};paths={}
 for sink,path in sorted(sink_paths.items()):
  if kinds.get(sink)!='SINK' or any(type(x) is not int or x<0 for x in [floors[sink],budgets[sink]]):raise ValueError('sink or RC bound')
  u=source;seen={source};value=0;path=tuple(path)
  for eid in path:
   a,b,w=index.arc(eid)
   if a!=u or b in seen or kinds.get(a)=='SINK' or kinds.get(b)=='SOURCE':raise ValueError('invalid rooted path')
   if b in parents and parents[b]!=(a,eid):raise ValueError('NET has multiple parents')
   parents[b]=(a,eid);nodes.add(b);seen.add(b);used.add(eid);value+=w;u=b
  if u!=sink or not floors[sink]<=value<=budgets[sink]:raise ValueError('sink endpoint or RC budget')
  costs[sink]=value;paths[sink]=path
 for node in nodes:
  if type(capacities.get(node)) is not int or capacities[node]<=0:raise ValueError('nonpositive or missing node capacity')
 return dict(nodes=frozenset(nodes),edge_ids=frozenset(used),parents=parents,paths=paths,sink_costs=costs,excess=sum(costs[s]-floors[s] for s in costs))
