"""Serial persistent owner snapshots; physical staging is not route admission.

Uses the existing independently checked PhysicalDelta predicate. Callers retain
responsibility for authentication, printed-route, canonical and timing gates.
"""
from collections import Counter
from types import MappingProxyType
from actual_change_physical_delta_v1_2026_10_18 import PhysicalDelta,net_unions

class Session:
 def __init__(self,paths,queries,inventory):
  # Store only logical identity fields used by physical validation.
  self.inventory=inventory
  self.state=PhysicalDelta(paths,self._queries(queries),inventory)
  self.generation=0;self.closed=False;self._pending={}
 @staticmethod
 def _queries(queries):
  return {cid:{k:q[k] for k in ('net_id','source','sink')} for cid,q in queries.items()}
 def prepare(self,paths,queries,inventory,*,generation):
  if self.closed or generation!=self.generation:raise RuntimeError('closed or stale owner generation')
  frozen_paths={cid:tuple(tuple(item) for item in path) for cid,path in paths.items()}
  frozen_queries=self._queries(queries)
  answer=self.state.evaluate(frozen_paths,frozen_queries,inventory)
  if answer['overflow_units']:raise ValueError('candidate owner state over capacity')
  changed=set(answer['changed_nets'])
  unions=dict(self.state.unions)
  subset={cid:path for cid,path in frozen_paths.items() if frozen_queries[cid]['net_id'] in changed}
  unions.update(net_unions(subset,{cid:frozen_queries[cid] for cid in subset},self.state.physical))
  occupancy={int(n):v for n,v in answer['node_occupancy'].items()}
  # Detached next snapshot, with unchanged physical inventory and predicates.
  candidate=object.__new__(PhysicalDelta)
  candidate.inventory_ref=inventory;candidate.digest=self.state.digest;candidate.physical=self.state.physical
  candidate.paths=MappingProxyType(frozen_paths)
  candidate.queries=MappingProxyType({cid:MappingProxyType(q) for cid,q in frozen_queries.items()})
  candidate.unions=MappingProxyType(unions);candidate.occupancy=MappingProxyType(occupancy)
  ticket=object()
  self._pending[ticket]=(self.generation,candidate)
  return ticket,dict(changed_connection_ids=answer['changed_connection_ids'],changed_nets=answer['changed_nets'],overflow_units=0)
 def commit(self,ticket,*,generation):
  if self.closed or generation!=self.generation:raise RuntimeError('closed or stale owner generation')
  if type(ticket) is not object or ticket not in self._pending:raise ValueError('unknown proposal ticket')
  epoch,candidate=self._pending[ticket]
  if epoch!=self.generation:raise RuntimeError('stale proposal')
  self.state=candidate;self.generation+=1;self._pending.clear()
  return self.generation
 def discard(self,ticket):
  if type(ticket) is not object or ticket not in self._pending:raise ValueError('unknown proposal ticket')
  del self._pending[ticket]
 def close(self):
  self.closed=True;self._pending.clear()
