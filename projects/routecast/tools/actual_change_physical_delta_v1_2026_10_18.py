"""Terminal-path physical delta; full printed-route and packed-pin gates remain."""
from collections import Counter,defaultdict
from types import MappingProxyType

def net_unions(paths,queries,physical):
 unions=defaultdict(set);parents=defaultdict(dict);roots={}
 if set(paths)!=set(queries):raise ValueError('Incomplete connection coverage')
 for cid,path in paths.items():
  q=queries[cid];net=q['net_id']
  if not path or path[0]!=(q['source'],None) or path[-1][0]!=q['sink']:raise ValueError('Endpoint mismatch')
  if net in roots and roots[net]!=q['source']:raise ValueError('Multiple NET roots')
  roots[net]=q['source'];seen=set()
  for index,(node,switch) in enumerate(path):
   if node not in physical.nodes or node in seen:raise ValueError('Unknown or cyclic node')
   seen.add(node);kind,capacity=physical.nodes[node]
   if int(capacity)<=0:raise ValueError('Disabled node')
   if index==0:
    if kind!='SOURCE':raise ValueError('Wrong SOURCE type')
   elif index==len(path)-1:
    if kind!='SINK':raise ValueError('Wrong SINK type')
   elif kind in ('SOURCE','SINK'):raise ValueError('Interior terminal')
   if index:
    parent=path[index-1][0]
    if (parent,node,switch) not in physical.arcs or switch not in physical.switches:raise ValueError('Absent physical arc')
    if kind!='SINK':
     edge=(parent,switch)
     if node in parents[net] and parents[net][node]!=edge:raise ValueError('Conflicting NET parents')
     parents[net][node]=edge
  unions[net].update(seen)
 return {net:frozenset(nodes) for net,nodes in unions.items()}

class PhysicalDelta:
 def __init__(self,paths,queries,inventory):
  self.inventory_ref=inventory
  self.digest=inventory.digest;self.physical=inventory.physical
  self.paths=MappingProxyType({cid:tuple(path) for cid,path in paths.items()})
  self.queries=MappingProxyType({cid:dict(q) for cid,q in queries.items()})
  self.unions=MappingProxyType(net_unions(self.paths,self.queries,self.physical))
  self.occupancy=MappingProxyType(dict(Counter(n for nodes in self.unions.values() for n in nodes)))
  if self.overflow(self.occupancy):raise ValueError('Old state over capacity')
 def overflow(self,occupancy):
  return sum(max(0,count-int(self.physical.nodes[node][1])) for node,count in occupancy.items())
 def evaluate(self,paths,queries,inventory):
  if inventory.digest!=self.digest or inventory is not self.inventory_ref:raise ValueError('Inventory epoch/object changed')
  if set(paths)!=set(self.paths) or set(queries)!=set(self.queries):raise ValueError('Changed coverage')
  for cid,q in queries.items():
   if q['net_id']!=self.queries[cid]['net_id']:raise ValueError('Changed NET identity')
  changed={cid for cid in paths if tuple(paths[cid])!=self.paths[cid] or queries[cid]!=self.queries[cid]}
  nets={queries[cid]['net_id'] for cid in changed}
  subset={cid:path for cid,path in paths.items() if queries[cid]['net_id'] in nets}
  new=net_unions(subset,{cid:queries[cid] for cid in subset},self.physical)
  occupancy=Counter(self.occupancy)
  for net in nets:
   occupancy.subtract(self.unions[net]);occupancy.update(new[net])
  if any(v<0 for v in occupancy.values()):raise ValueError('Negative occupancy')
  occupancy=+occupancy
  return dict(changed_connection_ids=sorted(changed),changed_nets=sorted(nets),node_occupancy={str(n):v for n,v in occupancy.items()},overflow_units=self.overflow(occupancy))
