"""Atomic insertion into capacity-legal retained native branch state.

Caller must validate physical arcs, pin identities, and RC budgets separately.
No failed or pending connection contributes pretend/zero occupancy.
"""
from collections import defaultdict
from incremental_shared_tree_ledger_v1 import SharedTreeLedger
class PartialSharedTreeLedger(SharedTreeLedger):
 def __init__(self,state,all_queries,capacities,length):
  if not set(state)<=set(all_queries):raise ValueError('retained CID outside target domain')
  roots=defaultdict(set)
  for q in all_queries.values():roots[q['net_id']].add(q['source'])
  if any(len(v)!=1 for v in roots.values()):raise ValueError('multiple sources for target NET')
  super().__init__(state,{cid:all_queries[cid] for cid in state},capacities,length)
  self.queries=all_queries
 def outside(self,cid,node):
  return self.occupancy[node]-int(node in self.nodes.get(self.queries[cid]['net_id'],{}))
 def insert(self,cid,path):
  if type(cid) is not int or cid not in self.queries or cid in self.state:raise ValueError('unknown or already present CID')
  path=tuple(tuple(x) for x in path);self._validate_endpoints(cid,path);net=self.queries[cid]['net_id']
  for n,_ in path:
   if self.occupancy[n]-int(n in self.nodes.get(net,{}))>=self.capacities[n]:raise ValueError('other-NET capacity conflict')
  for (u,_),(v,s) in zip(path,path[1:]):
   if v in self.parents.get(net,{}) and self.parents[net][v]!=(u,s):raise ValueError('retained parent conflict')
  # All failure checks precede the inherited deterministic additions.
  self._add(cid,path);self.state[cid]=path
