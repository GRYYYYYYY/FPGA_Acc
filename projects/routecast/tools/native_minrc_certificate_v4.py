"""Single capacity normalization per minRC call; immutable nonnegative integer RC.

Private checked execution consumes only normalized constraints. Both public APIs
validate before any native/Python dispatch. Exact arbitrary-integer fallback.
"""
import ctypes as C,json,time
from collections import Counter
from array import array
from pathlib import Path
from pre_route_endpoints import sha
from csr_integer_budget_search_bounded_v1 import query as fallback
U=C.c_uint64;P=C.POINTER(U);MAX=(1<<64)-1
class Result(C.Structure):
 _fields_=[(k,U) for k in ('status','cost','delay','created','expanded','examined','path_size')]
def pointer(values,ctype=U):return C.cast(values.buffer_info()[0],C.POINTER(ctype))
def fits(value):return type(value) is int and 0<=value<=MAX
class NativeMinRCCertificate:
 def __init__(self,rc):
  if not all(type(v) is int and v>=0 for v in rc.increments):raise ValueError("minRC requires nonnegative integer increments")
  length={}
  self.rc=rc;self.length=length;self.f=rc.fields;self.n=len(self.f['node_ids']);self.handle=None;self.native_calls=0;self.fallback_calls=0;self.preparation_seconds=0.;self.bindings={}
  root=Path(__file__).resolve().parents[1];directory=root/'build/native_minrc_certificate_v1_2026-10-08';receipt=directory/'receipt.json';b=json.loads(receipt.read_text());assert all(sha(f)==h for f,h in b['bindings'].items());self.bindings={**b['bindings'],str(receipt):sha(receipt)}
  values=rc.increments
  if not all(fits(x) for x in values) or not all(fits(x) for x in length.values()):return
  self.increment=array('Q',values);self.geometry=array('Q',(length.get(n,0) for n in range(self.n)))
  assert self.increment.itemsize==8 and list(self.increment)==values
  lib=C.CDLL(str(directory/'libroutecast_bounded.so'));self.lib=lib
  lib.rc_create.argtypes=[U,U]+[P]*7;lib.rc_create.restype=C.c_void_p
  lib.rc_destroy.argtypes=[C.c_void_p];lib.rc_destroy.restype=None
  lib.rc_query.argtypes=[C.c_void_p]+[U]*6+[P,C.POINTER(C.c_uint8),P,P,C.POINTER(Result)];lib.rc_query.restype=C.c_int
  lib.rc_copy_path.argtypes=[C.c_void_p,P,U];lib.rc_copy_path.restype=C.c_int
  arrays=[self.f[k] for k in ('row_offsets','dest_ranks','edge_ids','switch_ids')]+[self.increment,self.f['capacities'],self.geometry]
  assert all(a.typecode=='Q' and a.itemsize==8 for a in arrays)
  self.handle=lib.rc_create(self.n,len(values),*(pointer(a) for a in arrays))
  if not self.handle:raise ValueError('native CSR initialization rejected')
 def close(self):
  if self.handle:self.lib.rc_destroy(self.handle);self.handle=None
 def _capacity_constraints(self,source,outside):
  self.rc.node(source)
  initial=self.rc.initial(source)
  if type(initial) is not int or initial<0:raise ValueError('minRC requires nonnegative integer source delay')
  result=Counter()
  for node,count in outside.items():
   if type(node) is not int or not 0<=node<self.n:raise ValueError('Occupancy node outside immutable graph')
   if type(count) is not int or count<0:raise ValueError('Occupancy requires nonnegative integer counts')
   result[node]=min(count,self.f['capacities'][node])
  if result[source]>=self.f['capacities'][source]:raise ValueError('minRC source is blocked by capacity')
  return result
 def query(self,source,sink,budget,outside,kept,parents,max_labels,cost_limit_exclusive):
  outside=self._capacity_constraints(source,outside)
  return self._query_checked(source,sink,budget,outside,kept,parents,max_labels,cost_limit_exclusive)
 def _query_checked(self,source,sink,budget,outside,kept,parents,max_labels,cost_limit_exclusive):
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

 def query_with_certificate(self,source,sink,budget,outside,parents,max_labels):
  outside=self._capacity_constraints(source,outside)
  if type(budget) is not int or budget<0 or type(max_labels) is not int or max_labels<1:raise ValueError('invalid exact bounds')
  self.rc.node(source);self.rc.node(sink)
  assert outside[source]<self.f['capacities'][source]
  if self.rc.initial(source)>budget:
   answer=dict(status='NO_STRICT_IMPROVEMENT',physical_edge_ids=None,cost=None,delay=None,labels_created=0,labels_expanded=0,examined_edges=0)
   return answer,dict(clip=budget+1,potentials={})
  if not self.handle or not all(fits(x) for x in (self.rc.initial(source),budget,max_labels)):
   self.fallback_calls+=1
   return self._python_certificate(source,sink,budget,outside,parents,max_labels)
  answer=self._query_checked(source,sink,budget,outside,set(),parents,max_labels,1)
  if answer['status']=='LABEL_LIMIT':return answer,None
  lib=self.lib;lib.rc_potential_size.argtypes=[C.c_void_p,P];lib.rc_potential_size.restype=C.c_int
  lib.rc_copy_potentials.argtypes=[C.c_void_p,P,P,U];lib.rc_copy_potentials.restype=C.c_int
  size=U();assert lib.rc_potential_size(self.handle,C.byref(size))==0
  nodes=array('Q',[0])*size.value;values=array('Q',[0])*size.value
  assert lib.rc_copy_potentials(self.handle,pointer(nodes),pointer(values),size.value)==0
  clip=answer['delay'] if answer['status']=='FOUND' else budget+1
  return answer,dict(clip=clip,potentials={str(n):int(v) for n,v in zip(nodes,values)})
 def _python_certificate(self,source,sink,budget,outside,parents,max_labels):
  import heapq
  rc=self.rc;f=self.f;initial=rc.initial(source);created=expanded=examined=0;dist={};pred={};found=False;limited=False
  if initial<=budget:
   dist[source]=initial;created=1;queue=[(initial,source)];settled=set()
   while queue:
    value,u=heapq.heappop(queue)
    if u in settled or dist[u]!=value:continue
    settled.add(u);expanded+=1
    if u==sink:found=True;break
    for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
     examined+=1;v=f['dest_ranks'][slot]
     if outside[v]>=f['capacities'][v] or (v in parents and parents[v]!=(u,f['switch_ids'][slot])):continue
     nd=value+rc.increments[slot]
     if nd>budget or nd>=dist.get(v,nd+1):continue
     if created>=max_labels:limited=True;break
     dist[v]=nd;pred[v]=(u,slot);created+=1;heapq.heappush(queue,(nd,v))
    if limited:break
  status='LABEL_LIMIT' if limited else 'FOUND' if found else 'NO_STRICT_IMPROVEMENT';path=None
  if found:
   path=[];u=sink
   while u!=source:u,slot=pred[u];path.append(f['edge_ids'][slot])
   path.reverse();assert rc.path(source,sink,path)==dist[sink]
  answer=dict(status=status,physical_edge_ids=path,cost=0 if found else None,delay=dist[sink] if found else None,labels_created=created,labels_expanded=expanded,examined_edges=examined)
  if limited:return answer,None
  clip=dist[sink] if found else budget+1
  return answer,dict(clip=clip,potentials={str(n):d for n,d in sorted(dist.items()) if d<clip})
