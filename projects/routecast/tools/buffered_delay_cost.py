"""Exact additive RR delay weights only for buffered, zero-Cinternal graphs."""
from math import lcm
from fractions import Fraction
from path_rc import PathRC

class BufferedDelayCost:
 def __init__(self,graph):
  rc=PathRC(graph)
  if any(not buffered or internal for buffered,_,_,internal in rc.switches.values()):raise ValueError('requires every switch buffered with zero Cinternal')
  # Immutable serialized node timing and switch ID avoid repeated Fraction
  # hashes and exact arithmetic for every physical arc. Numeric validation
  # still comes from PathRC before any metadata is used as a cache key.
  cache={}
  for edge in graph.edges:
   key=(graph.nodes[edge.sink].timing,edge.switch_id)
   if key not in cache:
    r,c=rc.nodes[edge.sink];_,sr,intrinsic,_=rc.switches[edge.switch_id];cache[key]=(sr+r/2)*c+intrinsic
  denominator=1
  for d in cache.values():denominator=lcm(denominator,d.denominator)
  scaled={key:int(d*denominator) for key,d in cache.items()}
  self.graph=graph;self.denominator=denominator;self.weights=tuple(scaled[(graph.nodes[e.sink].timing,e.switch_id)] for e in graph.edges);self.nodes=rc.nodes
 def path_delay(self,source,edge_ids):
  if type(source) is not int or source not in self.nodes:raise ValueError('unknown source')
  current=source;seen={source};total=Fraction(0)
  for eid in edge_ids:
   if type(eid) is not int or not 0<=eid<len(self.weights):raise ValueError('invalid edge ID')
   edge=self.graph.edges[eid]
   if edge.source!=current or edge.sink in seen:raise ValueError('discontinuous or cyclic path')
   current=edge.sink;seen.add(current);total+=Fraction(self.weights[eid],self.denominator)
  r,c=self.nodes[source];return r*c/2+total
