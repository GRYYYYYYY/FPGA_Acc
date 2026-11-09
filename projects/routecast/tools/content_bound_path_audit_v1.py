"""Cache immutable physical/delay certificates; always recheck query/global constraints."""
from collections import defaultdict
from fractions import Fraction
from pre_route_endpoints import sha
from unified_rr_audit_inventory_v2 import read

class PathAudit:
 def __init__(self,graph,digest):
  self.graph=graph;self.digest=digest;self.inventory=read(graph,digest)
  self.certificates={};self.hits=0;self.misses=0
 def certificate(self,path):
  path=tuple(tuple(pair) for pair in path)
  if path in self.certificates:
   self.hits+=1;return self.certificates[path]
  inv=self.inventory
  assert path and path[0][1] is None
  assert all(type(n) is int and n in inv.physical.nodes and int(inv.physical.nodes[n][1])>0 for n,s in path)
  assert len({n for n,s in path})==len(path)
  r,c=inv.classes[inv.node_classes[path[0][0]]];delay=r*c/2
  parents=[]
  for (u,_),(v,s) in zip(path,path[1:]):
   assert type(s) is int and inv.arc_multiplicities.get((u,v,s))==1
   r,c=inv.classes[inv.node_classes[v]];sr,td=inv.electrical_switches[s]
   delay+=(sr+r/2)*c+td;parents.append((v,u,s))
  cert=(delay,tuple(n for n,s in path),tuple(parents))
  self.certificates[path]=cert;self.misses+=1;return cert
 def validate(self,paths,queries,budgets):
  # No stat-only graph trust or cached endpoint/budget/global acceptance.
  assert sha(self.graph)==self.digest
  assert set(paths)==set(queries)==set(budgets)
  owners=defaultdict(set);parents={}
  for cid,path in paths.items():
   query=queries[cid];path=tuple(tuple(pair) for pair in path)
   assert path and path[0]==(query['source'],None) and path[-1][0]==query['sink']
   delay,nodes,arcs=self.certificate(path)
   assert delay<=Fraction(budgets[cid])
   net=query['net_id']
   for n in nodes:owners[n].add(net)
   for v,u,s in arcs:
    key=(net,v);assert key not in parents or parents[key]==(u,s)
    parents[key]=(u,s)
  assert all(len(nets)<=int(self.inventory.physical.nodes[n][1]) for n,nets in owners.items())
  assert sha(self.graph)==self.digest
  return dict(connections=len(paths),unique_net_node_uses=sum(map(len,owners.values())))
