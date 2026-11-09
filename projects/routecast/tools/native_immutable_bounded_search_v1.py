"""Private lifetime-owned native CSR buffers for immutable Python contexts."""
import ctypes as C,json,time
from types import MappingProxyType
from array import array
from pathlib import Path
from pre_route_endpoints import sha
from csr_integer_budget_search_bounded_v1 import query as fallback
U=C.c_uint64;P=C.POINTER(U);MAX=(1<<64)-1
class Result(C.Structure):
 _fields_=[(k,U) for k in ('status','cost','delay','created','expanded','examined','path_size')]
def pointer(values,ctype=U):return C.cast(values.buffer_info()[0],C.POINTER(ctype))
def fits(value):return type(value) is int and 0<=value<=MAX
class NativeBoundedSearch:
 def __init__(self,rc,length):
  self.rc=rc;self.length=MappingProxyType(dict(length));self.f=rc.fields;self.n=len(self.f['node_ids']);self.handle=None;self.native_calls=0;self.fallback_calls=0;self.preparation_seconds=0.;self.bindings={}
  root=Path(__file__).resolve().parents[1];directory=root/'build/native_bounded_wire_search_v1_2026-10-08';receipt=directory/'receipt.json';b=json.loads(receipt.read_text());assert all(sha(f)==h for f,h in b['bindings'].items());self.bindings={**b['bindings'],str(receipt):sha(receipt)}
  values=rc.increments
  if not all(fits(x) for x in values) or not all(fits(x) for x in length.values()):return
  native_increment=array('Q',values);native_geometry=array('Q',(length.get(n,0) for n in range(self.n)))
  assert native_increment.itemsize==8 and tuple(native_increment)==tuple(values)
  lib=C.CDLL(str(directory/'libroutecast_bounded.so'));self.lib=lib
  lib.rc_create.argtypes=[U,U]+[P]*7;lib.rc_create.restype=C.c_void_p
  lib.rc_destroy.argtypes=[C.c_void_p];lib.rc_destroy.restype=None
  lib.rc_query.argtypes=[C.c_void_p]+[U]*6+[P,C.POINTER(C.c_uint8),P,P,C.POINTER(Result)];lib.rc_query.restype=C.c_int
  lib.rc_copy_path.argtypes=[C.c_void_p,P,U];lib.rc_copy_path.restype=C.c_int
  arrays=[array('Q',self.f[k]) for k in ('row_offsets','dest_ranks','edge_ids','switch_ids')]+[native_increment,array('Q',self.f['capacities']),native_geometry]
  self.__buffers=tuple(arrays)
  assert all(a.typecode=='Q' and a.itemsize==8 for a in arrays)
  self.handle=lib.rc_create(self.n,len(values),*(pointer(a) for a in arrays))
  if not self.handle:raise ValueError('native CSR initialization rejected')
 def close(self):
  if self.handle:self.lib.rc_destroy(self.handle);self.handle=None
 def query(self,source,sink,budget,outside,kept,parents,max_labels,cost_limit_exclusive):
  rc=self.rc;f=self.f;rc.node(source);rc.node(sink);initial=rc.initial(source)
  if type(budget) is not int or budget<0 or type(max_labels) is not int or max_labels<1 or type(cost_limit_exclusive) is not int or cost_limit_exclusive<0:raise ValueError('invalid exact bounds')
  if not self.handle or not all(fits(x) for x in (initial,budget,max_labels,cost_limit_exclusive)):
   self.fallback_calls+=1
   allowed=lambda u,i:outside[f['dest_ranks'][i]]<f['capacities'][f['dest_ranks'][i]] and (f['dest_ranks'][i] not in parents or parents[f['dest_ranks'][i]]==(u,f['switch_ids'][i]))
   cost=lambda u,i:0 if f['dest_ranks'][i] in kept else self.length.get(f['dest_ranks'][i],0)
   return fallback(rc,source,sink,budget,allowed,cost,max_labels=max_labels,cost_limit_exclusive=cost_limit_exclusive)
  if initial>budget or cost_limit_exclusive==0:
   return dict(status='NO_STRICT_IMPROVEMENT',physical_edge_ids=None,cost=None,delay=None,labels_created=0,labels_expanded=0,examined_edges=0)
  tick=time.perf_counter();occupancy=array('Q',[0])*self.n;mask=array('B',[0])*self.n;parent_source=array('Q',[0])*self.n;parent_switch=array('Q',[0])*self.n
  for n,v in outside.items():assert 0<=n<self.n and fits(v);occupancy[n]=v
  for n in kept:assert 0<=n<self.n;mask[n]=1
  for n,(u,s) in parents.items():assert 0<=n<self.n and 0<=u<self.n and fits(s+1);parent_source[n]=u+1;parent_switch[n]=s+1
  self.preparation_seconds+=time.perf_counter()-tick;out=Result();self.native_calls+=1
  code=self.lib.rc_query(self.handle,source,sink,initial,budget,cost_limit_exclusive,max_labels,pointer(occupancy),pointer(mask,C.c_uint8),pointer(parent_source),pointer(parent_switch),C.byref(out))
  if code:raise RuntimeError('native search failed with code '+str(code))
  status={0:'FOUND',1:'NO_STRICT_IMPROVEMENT',2:'LABEL_LIMIT'}[out.status];path=None;cost=delay=None
  if status=='FOUND':
   path=array('Q',[0])*out.path_size;assert self.lib.rc_copy_path(self.handle,pointer(path),len(path))==0;path=list(path);cost=out.cost;delay=out.delay
   assert rc.path(source,sink,path)==delay<=budget and cost<cost_limit_exclusive
  return dict(status=status,physical_edge_ids=path,cost=cost,delay=delay,labels_created=out.created,labels_expanded=out.expanded,examined_edges=out.examined)
