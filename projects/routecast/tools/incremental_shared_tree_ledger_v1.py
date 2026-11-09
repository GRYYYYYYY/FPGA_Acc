"""Per-branch reference counts for exact sameNET sharing and uniqueNET capacity.

This state utility supplies search constraints; physical RC, packed pins and STA
remain external obligations. Queries do not release or mutate any branch.
"""
from collections import Counter,defaultdict

class SharedTreeLedger:
 def __init__(self,state,queries,capacities,length):
  self.state={cid:tuple(tuple(x) for x in path) for cid,path in state.items()}
  self.queries=queries;self.capacities=capacities;self.length=length
  self.nodes=defaultdict(Counter);self.parents=defaultdict(dict)
  self.parent_uses=defaultdict(Counter);self.occupancy=Counter();self.wire=Counter()
  assert set(self.state)==set(queries)
  for cid,path in self.state.items():self._validate_endpoints(cid,path);self._add(cid,path)
  assert all(v<=capacities[n] for n,v in self.occupancy.items())
 def _validate_endpoints(self,cid,path):
  q=self.queries[cid]
  assert path and path[0]==(q['source'],None) and path[-1][0]==q['sink']
  assert len({n for n,s in path})==len(path) and all(type(n) is int and 0<=n<len(self.capacities) and self.capacities[n]>0 for n,s in path)
 def _add(self,cid,path):
  net=self.queries[cid]['net_id'];counts=self.nodes[net]
  for n,s in path:
   if counts[n]==0:self.occupancy[n]+=1;self.wire[net]+=self.length.get(n,0)
   counts[n]+=1
  for (u,_),(v,s) in zip(path,path[1:]):
   assert v not in self.parents[net] or self.parents[net][v]==(u,s)
   self.parents[net][v]=(u,s);self.parent_uses[net][v]+=1
 def view(self,cid):
  net=self.queries[cid]['net_id'];path=self.state[cid];moving={n for n,s in path}
  kept={n for n,c in self.nodes[net].items() if c>int(n in moving)}
  moving_parents={v for v,s in path[1:]}
  fixed={v:parent for v,parent in self.parents[net].items() if self.parent_uses[net][v]>int(v in moving_parents)}
  return kept,fixed
 def outside(self,cid,node):
  return self.occupancy[node]-int(node in self.nodes[self.queries[cid]['net_id']])
 def replace(self,cid,path):
  path=tuple(tuple(x) for x in path);self._validate_endpoints(cid,path)
  kept,fixed=self.view(cid);net=self.queries[cid]['net_id']
  assert all(self.outside(cid,n)<self.capacities[n] for n,s in path)
  for (u,_),(v,s) in zip(path,path[1:]):assert v not in fixed or fixed[v]==(u,s)
  # All failure checks precede mutation; only this branch's reference uses change.
  old=self.state[cid]
  for n,s in old:
   self.nodes[net][n]-=1
   if not self.nodes[net][n]:
    del self.nodes[net][n];self.occupancy[n]-=1;self.wire[net]-=self.length.get(n,0)
    if not self.occupancy[n]:del self.occupancy[n]
  for v,s in old[1:]:
   self.parent_uses[net][v]-=1
   if not self.parent_uses[net][v]:del self.parent_uses[net][v];del self.parents[net][v]
  self._add(cid,path);self.state[cid]=path
