"""Controlled archived native-path bridge; not a live feedback integration."""
import json
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
class Search:
 def __init__(self,f,rc,binary):
  self.f=f;self.rc=rc;self.slots={e:i for i,e in enumerate(f['edge_ids'])};self.phase=-1;self.used=set();self.groups=defaultdict(list)
  ep=R/'experiments/sha_second_swap_overflow_guard_complete_workflow_v1_2026-10-10/seed/demand/sha1/endpoints.json'
  from class_cached_rc_endpoint_context_v1 import load_endpoints
  _,_,_,original,_,queries=load_endpoints(ep)
  assert all(f[k]==original[k] for k in ['edge_ids','row_offsets','dest_ranks','capacities'])
  for q in queries:self.groups[q['net_id']].append(q)
  self.paths=[];self.prices=[]
  for phase in range(3):
   d=R/('experiments/sha_native_inprocess_hybrid_rr_v1_2026-10-10' if phase==0 else 'experiments/sha_native_inprocess_priced_rr_v2_2026-10-10')
   proof=json.loads((d/'receipt.json').read_text());assert all(sha(p)==h for p,h in proof['bindings'].items())
   observed={}
   for line in (d/('on' if phase==0 else f'round{phase-1}')/'floors.tsv').read_text().splitlines():
    x=line.split();cid,raw,count=map(int,x[1:4]);path=list(map(int,x[4:]));assert count==len(path) and cid not in observed;observed[cid]=(raw,path)
   assert set(observed)=={q['connection_id'] for q in queries}
   table={}
   for net,qs in self.groups.items():
    key=(qs[0]['source'],frozenset(q['sink'] for q in qs));assert key not in table
    table[key]=[(q,observed[q['connection_id']]) for q in qs]
   self.paths.append(table)
   self.prices.append({} if phase==0 else {int(a):int(b) for a,b in (l.split() for l in (R/f'experiments/native_inprocess_priced_prepare_v1_2026-10-10/prices{phase-1}.txt').read_text().splitlines())})
 def prepare(self,prices,weight):
  self.phase+=1;assert self.phase<3 and dict(prices)==self.prices[self.phase] and weight==(0 if self.phase==0 else 50000000);self.used=set()
 def search(self,source,sinks):
  key=(source,frozenset(sinks));assert key not in self.used;self.used.add(key);parents={};raw={source:self.rc.initial(source)};slots=self.slots
  for q,(delay,path) in self.paths[self.phase][key]:
   u=source;seen={u}
   for eid in path:
    slot=slots[eid];assert self.f['row_offsets'][u]<=slot<self.f['row_offsets'][u+1];v=self.f['dest_ranks'][slot];assert v not in seen;seen.add(v)
    assert v not in parents or parents[v]==(u,slot);parents[v]=(u,slot);u=v
   assert u==q['sink'] and self.rc.path(source,u,path)==delay;assert u not in raw or raw[u]==delay;raw[u]=delay
  return raw,parents,set(sinks)
 def close(self):pass
