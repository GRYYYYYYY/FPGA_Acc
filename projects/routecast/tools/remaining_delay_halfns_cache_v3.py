"""Budget-capped admissible sink-delay cache; h=min(exact distance, 0.5ns)."""
import hashlib,heapq,sys,time
from array import array
from pathlib import Path
from types import MappingProxyType
from pre_route_endpoints import sha
INF=(1<<64)-1
class DelayView:
 def __init__(self,data):self.values=memoryview(data).cast('Q')
 def get(self,node):
  value=self.values[node];return None if value==INF else value
class FrozenRC:
 def __init__(self,f,base):
  self.scale=base.scale;self.increments=tuple(base.increments);self.initials=tuple(base.initial(n) for n in range(len(f['node_ids'])));arcs=[None]*len(f['edge_ids'])
  for u in range(len(self.initials)):
   for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):arcs[f['edge_ids'][s]]=(u,f['dest_ranks'][s],self.increments[s])
  self.arcs=tuple(arcs)
 def initial(self,n):return self.initials[n]
 def path(self,source,sink,edges):
  node=source;value=self.initial(source);seen={node}
  for eid in edges:
   u,v,d=self.arcs[eid]
   if u!=node or v in seen:raise ValueError('invalid frozen path')
   node=v;seen.add(v);value+=d
  if node!=sink:raise ValueError('wrong frozen terminal')
  return value
class RemainingDelayCache:
 def __init__(self,graph,digest,fields,rc,workspace,max_entries=64):
  start=time.perf_counter();self.graph=Path(graph);self.digest=digest;self.fields=MappingProxyType({k:tuple(v) for k,v in fields.items()});self.rc=FrozenRC(self.fields,rc);self.cutoff=self.rc.scale//(2*10**9);self.n=len(self.fields['node_ids']);self.workspace=Path(workspace);self.workspace.mkdir();self.max_entries=max_entries
  if type(max_entries) is not int or max_entries<1:raise ValueError('positive capacity required')
  if sha(self.graph)!=digest:raise ValueError('graph identity changed')
  if max(self.rc.increments)*self.n+max(self.rc.initials)>=INF:raise ValueError('lattice overflow')
  reverse=[[] for _ in range(self.n)]
  for u in range(self.n):
   for s in range(self.fields['row_offsets'][u],self.fields['row_offsets'][u+1]):reverse[self.fields['dest_ranks'][s]].append((u,s))
  self.reverse=tuple(tuple(row) for row in reverse);self.entries={};self.hits=self.misses=self.evictions=self.aborted=0;self.events=[];self.validation_seconds=self.build_seconds=0.0
  h=hashlib.sha256()
  for seq in (self.fields['row_offsets'],self.fields['dest_ranks'],self.fields['capacities'],self.rc.increments,self.rc.initials):
   data=array('Q',seq)
   if sys.byteorder!='little':data.byteswap()
   h.update(data.tobytes())
  self._snapshot=(self.fields,self.rc,self.rc.increments,self.rc.initials,self.rc.arcs,self.rc.scale);self.model_digest=h.hexdigest();self.construction_seconds=time.perf_counter()-start
 def get(self,sink,deadline=None):
  tick=time.perf_counter()
  f,r,w,i,a,scale=self._snapshot
  if self.fields is not f or self.rc is not r or r.increments is not w or r.initials is not i or r.arcs is not a or r.scale!=scale:raise ValueError('cache model snapshot replaced')
  if type(sink) is not int or not 0<=sink<self.n or self.fields['capacities'][sink]<=0:raise ValueError('invalid sink')
  if sha(self.graph)!=self.digest:raise ValueError('cache graph changed')
  self.validation_seconds+=time.perf_counter()-tick
  if deadline is not None and time.perf_counter()>deadline:self.aborted+=1;raise TimeoutError('bound request deadline')
  if sink in self.entries:self.hits+=1;return self.entries[sink]
  self.misses+=1;start=time.perf_counter();dist=array('Q',[self.cutoff])*self.n;dist[sink]=0;queue=[(0,sink)];pops=0
  while queue:
   d,v=heapq.heappop(queue)
   if d!=dist[v]:continue
   pops+=1
   if pops%1024==0 and deadline is not None and time.perf_counter()>deadline:self.aborted+=1;self.build_seconds+=time.perf_counter()-start;raise TimeoutError('partial bound not published')
   for u,s in self.reverse[v]:
    if self.fields['capacities'][u]<=0:continue
    nd=d+self.rc.increments[s]
    if nd<dist[u]:dist[u]=nd;heapq.heappush(queue,(nd,u))
  if sha(self.graph)!=self.digest:raise ValueError('graph changed during bound build')
  # The immutable distance bytes are native endian in memory; archive little endian.
  data=dist.tobytes();archive=array('Q',dist)
  if sys.byteorder!='little':archive.byteswap()
  file=self.workspace/f'miss{self.misses}_sink{sink}.bin';file.write_bytes(archive.tobytes());view=DelayView(data)
  if len(self.entries)>=self.max_entries:del self.entries[next(iter(self.entries))];self.evictions+=1
  self.entries[sink]=view;elapsed=time.perf_counter()-start;self.build_seconds+=elapsed;self.events.append(dict(index=self.misses,sink=sink,sha256=sha(file),path=str(file),seconds=elapsed));return view
 def summary(self):return dict(graph_sha256=self.digest,model_sha256=self.model_digest,max_entries=self.max_entries,hits=self.hits,misses=self.misses,evictions=self.evictions,aborted=self.aborted,construction_seconds=self.construction_seconds,graph_validation_seconds=self.validation_seconds,build_and_archive_seconds=self.build_seconds,retained_distance_bytes=sum(v.values.nbytes for v in self.entries.values()),events=self.events,cutoff_integer=self.cutoff,scope='Capped h=min(distance,0.5ns), unreachable maps to cap. Full graph SHA checked every lookup; immutable fields/weights/initials snapshot. FIFO, no owner/path answers cached; partial timed-out miss never published.')
