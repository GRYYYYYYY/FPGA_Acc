"""Release/restore operations on isolated speculative shared-tree ledgers."""
from incremental_shared_tree_ledger_v1 import SharedTreeLedger

class TransactionLedger(SharedTreeLedger):
 def release(self,cid):
  # Missing-branch failure precedes every reference-count mutation.
  old=self.state[cid];net=self.queries[cid]['net_id']
  for n,s in old:
   self.nodes[net][n]-=1
   if not self.nodes[net][n]:
    del self.nodes[net][n];self.occupancy[n]-=1;self.wire[net]-=self.length.get(n,0)
    if not self.occupancy[n]:del self.occupancy[n]
  for v,s in old[1:]:
   self.parent_uses[net][v]-=1
   if not self.parent_uses[net][v]:del self.parent_uses[net][v];del self.parents[net][v]
  del self.state[cid]
 def insert(self,cid,path):
  assert cid not in self.state
  path=tuple(tuple(x) for x in path);self._validate_endpoints(cid,path)
  net=self.queries[cid]['net_id'];fixed=self.parents[net]
  assert all(self.outside(cid,n)<self.capacities[n] for n,s in path)
  for (u,_),(v,s) in zip(path,path[1:]):assert v not in fixed or fixed[v]==(u,s)
  # All topology/capacity assertions precede mutation. Physical arcs, RC and
  # packed pins are checked by the caller/independent experiment verifier.
  self._add(cid,path);self.state[cid]=path
