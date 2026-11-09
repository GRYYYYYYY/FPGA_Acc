"""Same MAP queue math as frozen bridge; native prepared integer/mask buffers."""
import time,struct
from fractions import Fraction
from compiled_prepared_map_tree_v1 import Graph as BaseGraph,Tree as BaseTree
from prepared_map_priority_v1 import Priority
class Graph(BaseGraph):
 def configure(self,query,mode,scale,queries):
  if mode not in ['H0','MAP']:raise ValueError('priority mode')
  self.query,self.mode,self.scale=query,mode,scale;self.cids={};self.heuristic_seconds=0.;self.heuristic_calls=0;self.terminal=tuple(k in ['IPIN','SINK'] for k in query.kinds)
  for q in queries:
   if query.connections[q['connection_id']]!=(q['source'],q['sink']):raise ValueError('query identity')
   self.cids.setdefault((q['source'],q['sink']),q['connection_id'])
class Tree(BaseTree):
 def expand(self,target,criticality,congestion,raw_budget):
  g=self.graph;q=g.query;cid=g.cids[self.source,target];tick=time.perf_counter();source,boundtarget=q.connections[cid]
  if q.data is None or source!=self.source or boundtarget!=target:raise ValueError('closed or changed endpoint')
  allowed=[k in ['CHANX','CHANY','IPIN','SINK'] or u==self.source or u in q.exits.get(self.source,set()) for u,k in enumerate(q.kinds)]
  if g.mode=='H0':priority=Priority(allowed)
  else:
   bits=struct.pack('>f',float(criticality)).hex()
   if Fraction.from_float(struct.unpack('>f',bytes.fromhex(bits))[0])!=criticality:raise ValueError('non-f32 criticality')
   offset=q.offset+q.targets[target]*q.n*8;row=q.data[offset:offset+q.n*8];priority=Priority.materialize(row,allowed,g.terminal,bits,g.scale,criticality.denominator)
  g.heuristic_seconds+=time.perf_counter()-tick;g.heuristic_calls+=1
  return super().expand(target,criticality,congestion,raw_budget,priority)
