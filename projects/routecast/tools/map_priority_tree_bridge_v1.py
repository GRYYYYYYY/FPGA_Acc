"""Four-argument tree adapter: priority only; current graph/frame CID binding."""
import struct,time
from fractions import Fraction
from compiled_map_weighted_tree_v1 import Graph as BaseGraph,Tree as BaseTree
from bound_native_map_query_v1 import f32
class Graph(BaseGraph):
 def configure(self,query,mode,scale,queries):
  if mode not in ['H0','MAP']:raise ValueError('priority mode')
  self.query,self.mode,self.scale=query,mode,scale;self.cids={};self.heuristic_seconds=0.;self.heuristic_calls=0
  for q in queries:
   if query.connections[q['connection_id']]!=(q['source'],q['sink']):raise ValueError('query identity')
   self.cids.setdefault((q['source'],q['sink']),q['connection_id'])
class Tree(BaseTree):
 def expand(self,target,criticality,congestion,raw_budget):
  g=self.graph;query=g.query;cid=g.cids[self.source,target];tick=time.perf_counter();allowed=[k in ['CHANX','CHANY','IPIN','SINK'] or u==self.source or u in query.exits.get(self.source,set()) for u,k in enumerate(query.kinds)];H=[0]*g.n
  if g.mode=='MAP':
   bits=struct.pack('>f',float(criticality)).hex()
   if Fraction.from_float(struct.unpack('>f',bytes.fromhex(bits))[0])!=criticality:raise ValueError('non-f32 criticality')
   kw=dict(graph_sha256=query.graph_sha256,endpoint_sha256=query.endpoint_sha256)
   for u,ok in enumerate(allowed):
    if ok:
     v=Fraction.from_float(f32(f32(1.2)*query.query(u,cid,bits,**kw)))*g.scale*criticality.denominator;H[u]=-(-v.numerator//v.denominator)
  g.heuristic_seconds+=time.perf_counter()-tick;g.heuristic_calls+=1
  return super().expand(target,criticality,congestion,raw_budget,H,allowed)
