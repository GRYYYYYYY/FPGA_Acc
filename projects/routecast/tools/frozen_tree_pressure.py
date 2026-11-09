"""Single-pass own-net excluded pressure on new tree branches only.

Uses the existing normalized factor1 halfbase rule and audited frozen net
union. Committed prefixes retain exact RC arrival charges, never accumulated
base/pressure. Adding nonnegative penalties preserves the base A* bound.
"""
import hashlib,json
from fractions import Fraction
from normalized_rc_net_pressure import NormalizedRCNetPressure
from astar_tree_reuse import AStarTreeReuse
from path_rc import PathRC,State

class FrozenTreePressure(NormalizedRCNetPressure):
 def __init__(self,graph,text,table_graph_sha256,prediction,scale=10**6):
  super().__init__(graph,text,table_graph_sha256,prediction,scale)
  weights=[None]*len(graph.edges)
  for arcs in self.base.outgoing.values():
   for eid,dst,w in arcs:weights[eid]=w
  rc=PathRC(graph)
  timing=[rc.step(State(Fraction(0),Fraction(0)),eid).delay/self.base.normalization*scale/2 for eid in range(len(graph.edges))]
  self.engine=AStarTreeReuse(graph,weights,timing)
  self.full={n:v for n,v in self.full.items() if v}
  self.context_prefix=hashlib.sha256(json.dumps(self.identity,sort_keys=True).encode())
 def penalties(self,net,source):
  if type(net) is not int or net not in self.roots or type(source) is not int or source!=self.roots[net]:raise ValueError('net source mismatch')
  result=dict(self.full)
  for n in self.users[net]:
   v=self.reduced[n]
   if v:result[n]=v
   else:result.pop(n,None)
  return result
 def route(self,net,source,sinks):
  penalties=self.penalties(net,source)
  context=self.context_prefix.copy();context.update(json.dumps({'net':net,'source':source,'own_nodes':sorted(self.users[net]),'rule':'ownexcluded_newbranch_only_RCprefix'},sort_keys=True).encode())
  return self.engine.route(source,sinks,penalties),context.hexdigest()
