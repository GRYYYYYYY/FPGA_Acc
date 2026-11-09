"""Authenticated-context caller wrapper for exact uint128 C++ Pareto search."""
import ctypes
from array import array
from pathlib import Path

class NativeCapacityRC:
 def __init__(self,rc):
  self.rc=rc;self.f=rc.fields;self.n=len(self.f['node_ids']);self.lib=ctypes.CDLL(str(Path(__file__).resolve().parents[1]/'build/rc_capacity_native_2026-10-06/search.so'))
  self.lib.rc_query.restype=ctypes.c_int;P=ctypes.POINTER(ctypes.c_uint64);Q=ctypes.c_uint64
  self.lib.rc_query.argtypes=[Q,*([P]*7),*([Q]*7),P,P]
  rows=self.f['row_offsets'];e=len(self.f['edge_ids'])
  if len(rows)!=self.n+1 or rows[0]!=0 or rows[-1]!=e or any(a>b for a,b in zip(rows,rows[1:])) or len(self.f['capacities'])!=self.n or any(len(v)!=e for v in (self.f['dest_ranks'],self.f['costs'],rc.increments)) or any(not 0<=v<self.n for v in self.f['dest_ranks']):raise ValueError('invalid CSR dimensions or destinations')
  self.arrays=[];self.ptrs=[]
  for values in [self.f[k] for k in ('row_offsets','dest_ranks','edge_ids','costs','capacities')]+[rc.increments]:
   if any(type(v) is not int or not 0<=v<(1<<64) for v in values):raise ValueError('uint64 transport required')
   a=array('Q',values);self.arrays.append(a);self.ptrs.append((Q*len(a)).from_buffer(a))
  self.other=array('Q',[0])*self.n;self.other_pointer=(Q*self.n).from_buffer(self.other);self.previous=set()
 def set_other(self,other):
  # Capture and validate one traversal before touching the published demand.
  # Zero entries still require validation; iteration failure preserves state.
  staged={}
  for n,v in other.items():
   if type(n) is not int or not 0<=n<self.n or type(v) is not int or not 0<=v<(1<<64):raise ValueError('invalid otherNET demand')
   if v:staged[n]=v
  previous=set(staged)
  for n in self.previous:self.other[n]=0
  for n,v in staged.items():self.other[n]=v
  self.previous=previous
 def query(self,source,sink,budget,max_labels=10000):
  self.rc.node(source);self.rc.node(sink);initial=self.rc.initial(source)
  if type(budget) is not int or not 0<=budget<(1<<128) or not 0<=initial<(1<<128) or type(max_labels) is not int or not 1<=max_labels<(1<<64):raise ValueError('uint128 budget and positive uint64 limit required')
  Q=ctypes.c_uint64;path=(Q*max_labels)();result=(Q*8)()
  code=self.lib.rc_query(self.n,*self.ptrs,self.other_pointer,source,sink,initial&((1<<64)-1),initial>>64,budget&((1<<64)-1),budget>>64,max_labels,path,result)
  statuses=['FOUND','UNREACHABLE','LABEL_LIMIT','ARITHMETIC_LIMIT','INVALID_INPUT','ALLOCATION_FAILURE'];status=statuses[code]
  found=code==0;edges=list(path[:result[3]]) if found else None;delay=(result[6]|(result[7]<<64)) if found else None
  if found and (self.rc.path(source,sink,edges)!=delay or delay>budget):raise ValueError('invalid native witness')
  return dict(status=status,physical_edge_ids=edges,cost=(result[4]|(result[5]<<64)) if found else None,delay=delay,labels_created=result[0],labels_expanded=result[1],examined_edges=result[2])
