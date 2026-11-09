"""Static query-edge antichains certified in one DAG bitset sweep."""
from exact_integer_global_timing_v1 import ExactGlobalTiming as Base

class ExactGlobalTiming(Base):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs)
  self.query_bits={cid:1<<i for i,cid in enumerate(sorted(self.groups))}
  self.prefix_bits={n:0 for n in self.order};self.repeated_queries=set()
  for u in self.order:
   for v,eid in self.adj[u]:
    if self.back[v] is None:continue
    bits=self.prefix_bits[u]
    if eid in self.connection_ids:
     cid=self.connection_ids[eid];bit=self.query_bits[cid]
     if bits&bit:self.repeated_queries.add(cid)
     bits|=bit
    self.prefix_bits[v]|=bits
  for cid,edges in self.groups.items():
   relevant=any(self.back[self.edges[eid]['sink']] is not None for eid in edges)
   if not relevant:self.multiplicities[cid]=0;continue
   if cid not in self.repeated_queries:self.multiplicities[cid]=1;continue
   # Repeated labels are supported by the original exact maximum-count DP;
   # the antichain shortcut never assumes K=1 for such a query.
   count={n:0 for n in self.order}
   for u in self.order:
    for v,eid in self.adj[u]:
     value=count[u]+int(eid in edges)
     if value>count[v]:count[v]=value
   self.multiplicities[cid]=max(count[n] for n in self.terminals)
 def topology_certificate(self):
  return dict(query_bit_indices={str(cid):bit.bit_length()-1 for cid,bit in self.query_bits.items()},prefix_bits={str(n):hex(value) for n,value in self.prefix_bits.items()},sink_reachable_nodes=sorted(n for n in self.order if self.back[n] is not None),multiplicities={str(cid):k for cid,k in self.multiplicities.items()},repeated_query_ids=sorted(self.repeated_queries),scope='Static enabled DAG/mapping only. Query edges not repeated on any sink path have K=1, proved by prefix-bit edge inequalities and attaining mapped edge. Repeated groups use full exact count DP; delay changes do not change this certificate. Topology or mapping changes invalidate it.')
