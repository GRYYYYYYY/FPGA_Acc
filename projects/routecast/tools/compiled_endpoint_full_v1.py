"""Cached typed physical graph, full NET base rebuild plus checked C++ propagation."""
import ctypes as C
from array import array
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];BINARY=R/'build/endpoint_full_v1_2026-10-20/full.so';MAX=2**64-1
class Graph:
 def __init__(self,node_ids,edges):
  self.ids=tuple(node_ids);self.ranks={n:i for i,n in enumerate(self.ids)}
  if not self.ids or len(self.ids)!=len(self.ranks) or any(type(n) is not int for n in self.ids):raise ValueError('unique integer RR IDs required')
  edges=list(edges)
  if any(a not in self.ranks or b not in self.ranks for a,b in edges):raise ValueError('unknown edge endpoint')
  self.sources=array('Q',(self.ranks[a] for a,b in edges));self.sinks=array('Q',(self.ranks[b] for a,b in edges));self.a=(C.c_uint64*len(edges)).from_buffer(self.sources);self.b=(C.c_uint64*len(edges)).from_buffer(self.sinks);self.lib=C.CDLL(str(BINARY));pointer=C.POINTER(C.c_uint64);self.lib.rc_endpoint_full.argtypes=[C.c_uint64,C.c_uint64,pointer,pointer,pointer,pointer];self.lib.rc_endpoint_full.restype=C.c_int
 def build_base(self,queries,NETs):
  queries=list(queries);groups=defaultdict(list);cids=set()
  for q in queries:
   cid=q['connection_id'];n=q['net_id'];s=q['source'];t=q['sink']
   if type(cid) is not int or cid<0 or cid in cids or s not in self.ranks or t not in self.ranks or n not in NETs:raise ValueError('query identity/domain')
   cids.add(cid);groups[n].append(q)
  if set(groups)!=set(NETs):raise ValueError('complete NET input required')
  base=array('Q',[0])*(5*len(self.ids))
  def add(index,value):
   if type(value) is not int or value<0 or base[index]+value>MAX:raise ValueError('unsigned64 base overflow')
   base[index]+=value
  for n,qs in groups.items():
   info=NETs[n];bbox=info['endpoint_bbox'];source=info['source_RR']
   if info['fanout']!=len(qs) or {q['source'] for q in qs}!={source} or len(bbox)!=4 or any(type(v) is not int for v in bbox) or bbox[2]<bbox[0] or bbox[3]<bbox[1]:raise ValueError('NET feature dimensions')
   span=bbox[2]-bbox[0]+bbox[3]-bbox[1]+2;index=self.ranks[source]*5;add(index,1);add(index+1,len(qs));add(index+2,span)
   for q in qs:index=self.ranks[q['sink']]*5;add(index+3,1);add(index+4,span)
  return base
 def propagate(self,base):
  if not isinstance(base,array) or base.typecode!='Q' or len(base)!=5*len(self.ids):raise ValueError('typed base layout')
  output=array('Q',[0])*(15*len(self.ids));x=(C.c_uint64*len(base)).from_buffer(base);y=(C.c_uint64*len(output)).from_buffer(output);rc=self.lib.rc_endpoint_full(len(self.ids),len(self.sources),self.a,self.b,x,y)
  if rc:raise ValueError('compiled full propagation rejected '+str(rc))
  return output
 def rebuild(self,queries,NETs):return self.propagate(self.build_base(queries,NETs))
 def unpack(self,values):return {n:list(values[i*15:(i+1)*15]) for i,n in enumerate(self.ids)}
