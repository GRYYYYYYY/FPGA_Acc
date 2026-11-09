"""Add atomic ordered-path restore/replacement to the source frontier prototype.

Caller supplies an immutable graph-edge checker bound to graph_epoch. Checks
cover node topology and shared NET trees, not RC budgets or route legality.
Removal and endpoint relocation semantics are inherited unchanged from v1.
"""
from collections import Counter,defaultdict
from retained_tree_frontier_state_v1 import Cache as RemovalCache,Record,State,View
from incremental_IPIN_feature_cache_v1 import lookup,patched

class Cache(RemovalCache):
 def __init__(self,graph_epoch,geometry,records,edge_exists):
  super().__init__(graph_epoch,geometry,records,edge_exists);self._edge_exists=edge_exists
 def prepare_paths(self,graph_epoch,generation,paths):
  before=self._state
  if graph_epoch!=self._epoch or type(generation) is not int or generation!=before.generation:raise ValueError('graph/generation mismatch')
  if not isinstance(paths,dict) or not paths:raise ValueError('nonempty path update mapping required')
  changes={};deltas=defaultdict(Counter);restored=replaced=0
  for cid,supplied in paths.items():
   old=lookup(before.queries,cid) if type(cid) is int else None
   if old is None:raise ValueError('unknown CID')
   if not isinstance(supplied,(list,tuple)):raise ValueError('ordered path schema')
   path=tuple(supplied)
   if len(path)<2 or path[0]!=old.source or path[-1]!=old.sink or any(type(n) is not int or n not in self._geometry for n in path) or len(set(path))!=len(path):raise ValueError('path endpoints/domain/cycle')
   if any(self._geometry[n][0] in ['SOURCE','SINK'] for n in path[1:-1]):raise ValueError('internal endpoint')
   if path==old.path:raise ValueError('unchanged path')
   if any(not self._edge_exists(a,b) for a,b in zip(path,path[1:])):raise ValueError('path RR edge')
   changes[cid]=Record(old.net,old.source,old.sink,path)
   if old.path is not None:deltas[old.net].subtract(old.path);replaced+=1
   else:restored+=1
   deltas[old.net].update(path)
  nets={};path_edges_checked=0
  for net,delta in deltas.items():
   oldnet=lookup(before.nets,net);parents={}
   for cid in oldnet.cids:
    r=changes.get(cid,lookup(before.queries,cid))
    if r.source!=oldnet.source:raise ValueError('NET source mismatch')
    if r.path is None:continue
    for a,b in zip(r.path,r.path[1:]):
     if b in parents and parents[b]!=a:raise ValueError('NET multiple parents')
     parents[b]=a;path_edges_checked+=1
   refs=Counter(oldnet.references)
   for n,d in delta.items():
    refs[n]+=d
    if refs[n]<0:raise ValueError('reference underflow')
    if not refs[n]:del refs[n]
   nets[net]=self._net(oldnet.source,oldnet.cids,refs)
  q,qp,qe=patched(before.queries,changes);n,np,ne=patched(before.nets,nets);after=State(before.generation+1,q,n)
  receipt=dict(generation=after.generation,path_updates=len(changes),restored_connections=restored,replaced_connections=replaced,touched_NETs=len(nets),NET_path_edges_checked=path_edges_checked,copied_shards=qp+np,copied_shard_entries=qe+ne)
  token=object();self._pending[token]=(before,after,receipt);return token
