"""Serial source-only retained-path frontier approximation with COW publication.

Ordered paths are checked against caller-authenticated graph edges. Frontiers
contain SOURCE/OPIN/CHANX/CHANY nodes still owned by retained sibling paths,
plus the current SOURCE. They omit native spatial, cost and bounding-box filters.
No route is supplied for removed queries; geometry is not route admission.
"""
from collections import Counter,defaultdict,namedtuple
from types import MappingProxyType
from incremental_IPIN_feature_cache_v1 import pages,lookup,patched

Record=namedtuple('Record','net source sink path')
Net=namedtuple('Net','source cids references frontier')
State=namedtuple('State','generation queries nets')
EXPAND=frozenset(['SOURCE','OPIN','CHANX','CHANY'])

class View:
 def __init__(self,state,geometry,epoch,published):self.__state=state;self.__geometry=geometry;self.__epoch=epoch;self.__published=published
 @property
 def graph_epoch(self):return self.__epoch
 @property
 def published(self):return self.__published
 @property
 def generation(self):return self.__state.generation
 def query(self,cid):
  r=lookup(self.__state.queries,cid)
  if r is None:raise ValueError('unknown CID')
  return dict(connection_id=cid,net_id=r.net,source=r.source,sink=r.sink,path=r.path)
 def frontier(self,cid):
  r=self.query(cid);return lookup(self.__state.nets,r['net_id']).frontier
 def feature(self,cid):
  r=self.query(cid)
  if r['path'] is not None:raise ValueError('feature requires removed/unrouted CID')
  nodes=self.frontier(cid);sink=self.__geometry[r['sink']];same=[self.__geometry[n] for n in nodes if self.__geometry[n][5]==sink[5]]
  distance=min((max(0,a[1]-sink[2],sink[1]-a[2])+max(0,a[3]-sink[4],sink[3]-a[4]) for a in same),default=None)
  return dict(graph_epoch=self.graph_epoch,published=self.published,generation=self.generation,connection_id=cid,net_id=r['net_id'],retained_path=r['path'] is not None,frontier_nodes=len(nodes),same_layer_frontier_nodes=len(same),min_tile_L1=distance)
 def snapshot(self):
  return dict(graph_epoch=self.graph_epoch,published=self.published,generation=self.generation,queries={c:self.query(c) for p in self.__state.queries for c in p},nets={n:dict(source=v.source,cids=v.cids,references=dict(v.references),frontier=v.frontier) for p in self.__state.nets for n,v in p.items()})

class Cache:
 def __init__(self,graph_epoch,geometry,records,edge_exists):
  if not isinstance(graph_epoch,str) or not graph_epoch:raise ValueError('graph epoch')
  if not callable(edge_exists):raise ValueError('edge checker required')
  self._epoch=graph_epoch;geo={}
  for n,v in geometry.items():
   if type(n) is not int or n<0 or not isinstance(v,(list,tuple)) or len(v)!=6:raise ValueError('geometry schema')
   kind,x0,x1,y0,y1,layer=v
   if kind not in EXPAND|{'IPIN','SINK'} or any(type(k) is not int or k<0 for k in v[1:]) or x0>x1 or y0>y1:raise ValueError('node rectangle')
   geo[n]=tuple(v)
  self._geometry=MappingProxyType(geo);queries={};by_net=defaultdict(list);parents=defaultdict(dict)
  for row in records:
   if set(row)!={'connection_id','net_id','source','sink','path'}:raise ValueError('record schema')
   cid,net,src,sink=[row[k] for k in ['connection_id','net_id','source','sink']]
   if any(type(k) is not int or k<0 for k in [cid,net,src,sink]) or cid in queries:raise ValueError('identity')
   self._endpoint(src,'SOURCE');self._endpoint(sink,'SINK')
   if not isinstance(row['path'],(list,tuple)):raise ValueError('ordered path schema')
   path=tuple(row['path'])
   if len(path)<2 or path[0]!=src or path[-1]!=sink or any(type(n) is not int or n not in geo for n in path) or len(set(path))!=len(path):raise ValueError('ordered path endpoints/cycle')
   if any(geo[n][0] in ['SOURCE','SINK'] for n in path[1:-1]):raise ValueError('internal endpoint')
   for a,b in zip(path,path[1:]):
    if not edge_exists(a,b):raise ValueError('path RR edge')
    if b in parents[net] and parents[net][b]!=a:raise ValueError('NET multiple parents')
    parents[net][b]=a
   queries[cid]=Record(net,src,sink,path);by_net[net].append(cid)
  nets={}
  for net,cids in by_net.items():
   sources={queries[c].source for c in cids}
   if len(sources)!=1:raise ValueError('NET source mismatch')
   refs=Counter(n for c in cids for n in queries[c].path);nets[net]=self._net(next(iter(sources)),frozenset(cids),refs)
  self._state=State(0,pages(queries),pages(nets));self._pending={}
 def _endpoint(self,node,kind):
  if type(node) is not int or node not in self._geometry or self._geometry[node][0]!=kind:raise ValueError('endpoint type/domain')
 def _net(self,source,cids,refs):
  refs={n:c for n,c in refs.items() if c};assert all(c>0 for c in refs.values());frontier=frozenset([source])|frozenset(n for n in refs if self._geometry[n][0] in EXPAND)
  return Net(source,cids,MappingProxyType(refs),frontier)
 @property
 def generation(self):return self._state.generation
 def view(self):return View(self._state,self._geometry,self._epoch,True)
 def prepare(self,graph_epoch,generation,remove_cids,sink_updates=None,source_updates=None):
  before=self._state
  if graph_epoch!=self._epoch or type(generation) is not int or generation!=before.generation:raise ValueError('graph/generation mismatch')
  removals=tuple(remove_cids);sink_updates=dict(sink_updates or {});source_updates=dict(source_updates or {})
  if len(set(removals))!=len(removals) or any(type(c) is not int or lookup(before.queries,c) is None for c in removals):raise ValueError('removal domain/duplicates')
  removed=set(removals);invalidated=[]
  for net,src in source_updates.items():
   old=lookup(before.nets,net) if type(net) is int else None
   if old is None:raise ValueError('unknown source NET')
   self._endpoint(src,'SOURCE')
   if src==old.source:raise ValueError('unchanged source update')
   removed.update(old.cids);invalidated.append(net)
  for cid,sink in sink_updates.items():
   if type(cid) is not int or lookup(before.queries,cid) is None or cid not in removed:raise ValueError('sink edit must remove known CID')
   self._endpoint(sink,'SINK')
  if not removed:raise ValueError('empty batch')
  changes={};deltas=defaultdict(Counter);meaningful=False
  for cid in removed:
   old=lookup(before.queries,cid);new=Record(old.net,source_updates.get(old.net,old.source),sink_updates.get(cid,old.sink),None);changes[cid]=new;meaningful|=old!=new
   if old.path is not None:deltas[old.net].subtract(old.path)
  if not meaningful:raise ValueError('no state change')
  touched={r.net for r in changes.values()};nets={}
  for net in touched:
   old=lookup(before.nets,net);refs=Counter(old.references)
   for n,d in deltas[net].items():
    refs[n]+=d
    if refs[n]<0:raise ValueError('reference underflow')
    if not refs[n]:del refs[n]
   src=source_updates.get(net,old.source)
   if net in source_updates and refs:raise ValueError('source change retained old paths')
   nets[net]=self._net(src,old.cids,refs)
  q,qp,qe=patched(before.queries,changes);n,np,ne=patched(before.nets,nets);after=State(before.generation+1,q,n)
  receipt=dict(generation=after.generation,removed_connections=len(changes),touched_NETs=len(nets),whole_NET_source_invalidations=tuple(sorted(invalidated)),copied_shards=qp+np,copied_shard_entries=qe+ne)
  token=object();self._pending[token]=(before,after,receipt);return token
 def preview(self,token):
  if token not in self._pending:raise ValueError('foreign/consumed ticket')
  return View(self._pending[token][1],self._geometry,self._epoch,False)
 def commit(self,token):
  if token not in self._pending:raise ValueError('foreign/consumed ticket')
  before,after,receipt=self._pending.pop(token)
  if before is not self._state:raise ValueError('stale ticket')
  self._state=after;return dict(receipt)
 def abort(self,token):
  if token not in self._pending:raise ValueError('foreign/consumed ticket')
  self._pending.pop(token)
