"""No skips: unique full price dependencies retained independently of cache eviction."""
from pathlib import Path
from array import array
import ctypes as C
import json,hashlib,os
from price_dependency_search_cache_v2 import Search as Base
from soft_demand_workspace_bridge_v1 import Search as Forward
from bidirectional_rc_bridge_v1 import Bidirectional
class Search(Base):
 def __init__(self,fields,rc,binary):
  super().__init__(fields,rc,entries=0,read_limit=len(fields['capacities']),output_limit=2**32)
  self.forward.close();self.bidi.close();b=Path(__file__).resolve().parents[1]/'build/monotone_relax_trace_v1_2026-10-10'
  self.forward=Forward(self.fields,self.rc,b/'forward.so');self.bidi=Bidirectional(self.fields,self.rc,b/'bidi.so')
  for s in [self.forward,self.bidi]:
   s.lib.rc_reads_begin.argtypes=[C.c_uint64];s.lib.rc_reads_begin.restype=None;s.lib.rc_reads_complete.restype=C.c_int;s.lib.rc_reads_count.restype=C.c_uint64;s.lib.rc_reads_at.argtypes=[C.c_uint64];s.lib.rc_reads_at.restype=C.c_uint64;s.lib.rc_reads_begin_domain.argtypes=[C.c_uint64,C.c_uint64];s.lib.rc_reads_begin_domain.restype=C.c_int
   assert s.lib.rc_reads_begin_domain(self.n,self.n)==0
  self.monotone_pairs={};self.history={};self.rows=[];self.phase=-1;path=Path(os.environ['ROUTECAST_SHADOW_DIAG_OUTPUT']);path.parent.mkdir(parents=True,exist_ok=True);self.dep_path=path.with_suffix('.dependencies.bin');self.dep_file=self.dep_path.open('wb')
 def prepare(self,prices,weight):
  super().prepare(prices,weight)
  if hasattr(self,'phase'):self.phase+=1
 def search(self,source,sinks):
  targets=tuple(sorted(set(sinks)));key=(source,targets,self.weight);old=self.history.get(key);reason='NO_PRIOR_CONTEXT';changed=[]
  if old is not None:
   d,p,_,_=old;pair=(id(p),id(self.prices))
   if pair not in self.monotone_pairs:self.monotone_pairs[pair]=all(x<=y for x,y in zip(p,self.prices))
   changed=[u for u in d if p[u]!=self.prices[u]];reason='PRICE_DECREASE' if not self.monotone_pairs[pair] else ('DEPENDENCY_PRICE_CHANGED' if changed else 'CERTIFICATE_VALID')
  result=super().search(source,targets);s=self.bidi if len(targets)==1 else self.forward
  assert s.lib.rc_reads_complete(),'full-domain unique collection must complete'
  d=array('I',(s.lib.rc_reads_at(i) for i in range(s.lib.rc_reads_count())));assert len(d)==len(set(d)) and len(d)<=self.n
  raw,parents,found=result;paths=[]
  for t in sorted(found):
   u=t;path=[]
   while u!=source:prev,e=parents[u];path.append(e);u=prev;assert len(path)<=self.n
   paths.append([t,raw[t],list(reversed(path))])
  digest=hashlib.sha256(json.dumps(paths,separators=(',',':')).encode()).hexdigest()
  if reason=='CERTIFICATE_VALID':assert digest==old[2]
  offset=self.dep_file.tell();d.tofile(self.dep_file)
  self.rows.append(dict(dependency_offset=offset,old_row=old[3] if old else None,phase=self.phase,source=source,targets=targets,weight=self.weight,reason=reason,old_dependencies=len(old[0]) if old else None,changed_count=len(changed),first_changed_node=min(changed) if changed else None,dependencies=len(d),output_digest=digest))
  self.history[key]=(d,self.prices,digest,len(self.rows)-1)
  return result
 def close(self):
  self.dep_file.close();path=Path(os.environ['ROUTECAST_SHADOW_DIAG_OUTPUT']);path.parent.mkdir(parents=True,exist_ok=True)
  from collections import Counter
  path.write_text(json.dumps(dict(dependency_path=str(self.dep_path.resolve()),dependency_sha256=hashlib.sha256(self.dep_path.read_bytes()).hexdigest(),dependency_itemsize=array('I').itemsize,rows=self.rows,counts=dict(Counter(r['reason'] for r in self.rows)),history_contexts=len(self.history),history_dependency_bytes=sum(len(v[0])*v[0].itemsize for v in self.history.values()),scope='All searches executed; complete successful-relax/post-verification dependencies under monotone prices retained without eviction, fresh endogenous price vectors. No cached outputs, native or performance claim.'),indent=2)+'\n');super().close()
