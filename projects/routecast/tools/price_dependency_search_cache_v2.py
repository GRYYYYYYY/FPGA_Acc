"""Serial, instance-bound requested-output cache over standalone128 traced kernels."""
from pathlib import Path
from types import SimpleNamespace
from collections import OrderedDict,Counter
import ctypes as C
import copy
from soft_demand_workspace_bridge_v1 import Search as Forward
from bidirectional_rc_bridge_v1 import Bidirectional
R=Path(__file__).resolve().parents[1]
class Search:
 def __init__(self,fields,rc,*,entries=128,read_limit=65536,output_limit=65536,dependency_total_limit=1048576,output_total_limit=262144):
  if any(not isinstance(v,int) or v<0 for v in [entries,read_limit,output_limit,dependency_total_limit,output_total_limit]) or read_limit>=2**64:raise ValueError('invalid cache limit')
  # Private immutable-by-contract kernel inputs: later caller mutations cannot rebind a cached context.
  self.fields={k:tuple(fields[k]) for k in ['row_offsets','dest_ranks','capacities']};self.n=len(self.fields['capacities']);initial=tuple(rc.initial(u) for u in range(self.n));self.rc=SimpleNamespace(increments=tuple(rc.increments),initial=initial.__getitem__)
  b=R/'build/price_read_trace_v2_2026-10-10';self.forward=Forward(self.fields,self.rc,b/'forward.so');self.bidi=Bidirectional(self.fields,self.rc,b/'bidi.so')
  self.entries,self.read_limit,self.output_limit=entries,read_limit,output_limit;self.cache=OrderedDict();self.dependency_total_limit=dependency_total_limit;self.output_total_limit=output_total_limit;self.dependency_items=0;self.output_items=0;self.stats=Counter();self.closed=False;self.prepare({},0)
  for s in [self.forward,self.bidi]:
   s.lib.rc_reads_begin.argtypes=[C.c_uint64];s.lib.rc_reads_begin.restype=None;s.lib.rc_reads_complete.restype=C.c_int;s.lib.rc_reads_count.restype=C.c_uint64;s.lib.rc_reads_at.argtypes=[C.c_uint64];s.lib.rc_reads_at.restype=C.c_uint64
 def prepare(self,prices,weight):
  if self.closed:raise RuntimeError('closed')
  # Validate both kernels' stricter envelope before either mutable prepare.
  values=tuple(prices.get(u,0) for u in range(self.n))
  if not isinstance(weight,int) or not 0<=weight<2**64 or any(not isinstance(v,int) or not 0<=v<2**64 for v in values):raise ValueError('invalid price/weight')
  if 2*self.n*(self.forward.maxinc+weight*max(values,default=0))+max(self.rc.initial(u) for u in range(self.n))>=2**120:raise ValueError('cost envelope exceeded')
  current=dict(enumerate(values));self.forward.prepare(current,weight);self.bidi.prepare(current,weight);self.prices=values;self.weight=weight
 def search(self,source,sinks):
  if self.closed:raise RuntimeError('closed')
  targets=tuple(sorted(set(sinks)));key=(source,targets,self.weight)
  old=self.cache.get(key)
  if old is not None and all(self.prices[u]==v for u,v in old[0]):
   self.stats['hits']+=1;self.cache.move_to_end(key);return copy.deepcopy(old[1])
  self.stats['misses']+=1;self._remove(key)
  s=self.bidi if len(targets)==1 else self.forward;s.lib.rc_reads_begin(self.read_limit)
  try:
   if len(targets)==1:
    t=targets[0];a=s.search(source,t);raw={};parents={};found=set()
    if a is not None:
     raw={source:self.rc.initial(source),t:a['raw']};u=source
     for e in a['slots']:
      v=self.fields['dest_ranks'][e];parents[v]=(u,e);u=v
     found={t}
   else:
    arr,p,found=s.search(source,targets);raw={source:self.rc.initial(source)};parents={}
    for t in sorted(found):
     raw[t]=arr[t];u=t;steps=0
     while u!=source:
      prev,e=p[u];parents[u]=(prev,e);u=prev;steps+=1
      if steps>self.n:raise RuntimeError('invalid parent cycle')
   result=(raw,parents,set(found))
  except Exception:
   self.stats['errors']+=1;raise
  if not s.lib.rc_reads_complete():self.stats['incomplete']+=1;return result
  if len(raw)+len(parents)+len(found)>self.output_limit:self.stats['oversize_output']+=1;return result
  if self.entries:
   dependency=tuple((u,self.prices[u]) for u in sorted({s.lib.rc_reads_at(i) for i in range(s.lib.rc_reads_count())}))
   size=len(raw)+len(parents)+len(found)
   if len(dependency)>self.dependency_total_limit or size>self.output_total_limit:self.stats['oversize_total']+=1;return result
   self.cache[key]=(dependency,copy.deepcopy(result));self.dependency_items+=len(dependency);self.output_items+=size
   while len(self.cache)>self.entries or self.dependency_items>self.dependency_total_limit or self.output_items>self.output_total_limit:
    self._remove(next(iter(self.cache)));self.stats['evictions']+=1
   self.stats['peak_dependency_items']=max(self.stats['peak_dependency_items'],self.dependency_items)
   self.stats['peak_output_items']=max(self.stats['peak_output_items'],self.output_items)
  return result
 def _remove(self,key):
  old=self.cache.pop(key,None)
  if old is not None:
   self.dependency_items-=len(old[0]);self.output_items-=sum(len(x) for x in old[1])
 def close(self):
  self.forward.close();self.bidi.close();self.cache.clear();self.dependency_items=self.output_items=0;self.closed=True
