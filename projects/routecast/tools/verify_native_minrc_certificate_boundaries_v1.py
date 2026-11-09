"""Independent Bellman-Ford minima and clipped-potential boundary checks."""
import json
from array import array
from collections import Counter
from pathlib import Path
from pre_route_endpoints import sha
from native_minrc_certificate_v1 import NativeMinRCCertificate,MAX
R=Path(__file__).resolve().parents[1];D=R/'experiments/native_minrc_certificate_boundaries_v1_2026-10-08';D.mkdir(exist_ok=False)
class RC:
 def __init__(self,initial,adj):
  self.value=initial;self.increments=[];row=[0];dest=[];sources=[]
  for u,edges in enumerate(adj):
   for v,w in edges:dest.append(v);sources.append(u);self.increments.append(w)
   row.append(len(dest))
  self.sources=sources;n=len(adj)
  self.fields={k:array('Q',v) for k,v in dict(node_ids=list(range(n)),row_offsets=row,dest_ranks=dest,edge_ids=list(range(len(dest))),switch_ids=[0]*len(dest),capacities=[1]*n).items()}
 def node(self,n):assert type(n) is int and 0<=n<len(self.fields['node_ids']);return 0,0
 def initial(self,n):self.node(n);return self.value if n==0 else 0
 def path(self,source,sink,edges):
  value=self.initial(source);u=source
  for e in edges:assert self.sources[e]==u;u=self.fields['dest_ranks'][e];value+=self.increments[e]
  assert u==sink;return value
cases=[('maximum_found',MAX-4,[[(1,4)],[]],MAX,100,{}, {},'FOUND'),
 ('overflow_exhaustion',MAX-4,[[(1,5)],[]],MAX,100,{}, {},'NO_STRICT_IMPROVEMENT'),
 ('large_increment_fallback',0,[[(1,MAX+1)],[]],MAX+1,100,{}, {},'FOUND'),
 ('large_initial_fallback',MAX+1,[[(1,0)],[]],MAX+1,100,{}, {},'FOUND'),
 ('zero_delay',0,[[(1,0)],[]],0,100,{}, {},'FOUND'),
 ('label_limit',0,[[(1,1)],[]],1,1,{}, {},'LABEL_LIMIT'),
 ('capacity_blocked',0,[[(1,1)],[]],10,100,{1:1}, {},'NO_STRICT_IMPROVEMENT'),
 ('parent_blocked',0,[[(1,1)],[]],10,100,{}, {1:(1,0)},'NO_STRICT_IMPROVEMENT'),
 ('branched_zero_cycle',2,[[(1,2),(2,1)],[(2,0),(3,2)],[(1,0),(3,5)],[]],10,100,{}, {},'FOUND'),
 ('source_above_budget',5,[[(1,1)],[]],4,100,{}, {},'NO_STRICT_IMPROVEMENT')]
bindings={str(Path(__file__)):sha(Path(__file__)),str(R/'tools/native_minrc_certificate_v1.py'):sha(R/'tools/native_minrc_certificate_v1.py')};rows=[]
def verify(rc,budget,outside,parents,result,cert):
 if result['status']=='LABEL_LIMIT':assert cert is None;return
 dist={0:rc.initial(0)} if rc.initial(0)<=budget else {};f=rc.fields
 for _ in range(len(f['node_ids'])):
  old=dict(dist)
  for e,u in enumerate(rc.sources):
   v=f['dest_ranks'][e]
   if u not in old or outside[v]>=f['capacities'][v] or (v in parents and parents[v]!=(u,0)):continue
   nd=old[u]+rc.increments[e]
   if nd<=budget and nd<dist.get(v,nd+1):dist[v]=nd
  if dist==old:break
 sink=len(f['node_ids'])-1;found=sink in dist
 assert found==(result['status']=='FOUND')
 clip=dist[sink] if found else budget+1
 expected={str(n):v for n,v in dist.items() if v<clip}
 assert cert==dict(clip=clip,potentials=expected)
 if found:assert rc.path(0,sink,result['physical_edge_ids'])==dist[sink]==result['delay']
 assert cert['potentials'].get('0',clip)==min(rc.initial(0),clip)
 for e,u in enumerate(rc.sources):
  v=f['dest_ranks'][e]
  if outside[v]<f['capacities'][v] and (v not in parents or parents[v]==(u,0)):
   assert expected.get(str(v),clip)<=expected.get(str(u),clip)+rc.increments[e]
for name,initial,adj,budget,limit,occ,parents,status in cases:
 rc=RC(initial,adj);native=NativeMinRCCertificate(rc);bindings.update(native.bindings)
 result,cert=native.query_with_certificate(0,len(adj)-1,budget,Counter(occ),parents,limit)
 assert result['status']==status;verify(rc,budget,Counter(occ),parents,result,cert)
 # Reuse the same native context after a successful search: no stale export
 # may survive an immediate source-budget rejection or incomplete search.
 if native.handle:
  rc.value=budget+1
  second,sc=native.query_with_certificate(0,len(adj)-1,budget,Counter(occ),parents,limit)
  assert sc==dict(clip=budget+1,potentials={});assert second['status']=='NO_STRICT_IMPROVEMENT'
 rows.append(dict(case=name,result=result,certificate=cert,fallback_calls=native.fallback_calls));native.close()
assert all(sha(path)==digest for path,digest in bindings.items())
out=dict(bindings=bindings,all10_integer_constraints_minima_and_certificate_cases_pass=True,rows=rows,
 scope='Synthetic independent full-graph Bellman-Ford plus clipped-potential arc inequalities. Includes uint64 maximum, overflow rejection, arbitrary-integer fallback, zero cycles, source-budget rejection/context reuse, fixed parents, capacity and incomplete label-limit no-certificate contract. Not physical FPGA/native STA evidence.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print('PASS10 exact minRC certificate boundary cases',flush=True)
