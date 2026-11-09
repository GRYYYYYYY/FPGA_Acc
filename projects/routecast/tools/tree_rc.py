"""Exact-decimal rooted-tree RC oracle from serialized RR electrical metadata.

Mirrors local VPR route_tree C_downstream/Tdel equations, not native float
parity or atom STA. Rejects aliases/reconvergence/disconnected/cyclic unions.
"""
from collections import defaultdict
from fractions import Fraction
from types import MappingProxyType
from path_rc import PathRC

class TreeRC:
 def __init__(self,graph):
  self.graph=graph;rc=PathRC(graph);self.nodes=rc.nodes;self.switches=rc.switches
 def evaluate(self,source,edge_ids):
  if type(source) is not int or source not in self.nodes:raise ValueError('unknown source')
  ids=list(edge_ids)
  if any(type(e) is not int or not 0<=e<len(self.graph.edges) for e in ids):raise ValueError('invalid edge ID')
  children=defaultdict(list);parent={};nodes={source}
  for eid in sorted(set(ids)):
   edge=self.graph.edges[eid]
   if edge.sink==source or edge.sink in parent:raise ValueError('root incoming or multiple parents')
   parent[edge.sink]=eid;children[edge.source].append(eid);nodes.update((edge.source,edge.sink))
  order=[];stack=[source];seen=set()
  while stack:
   node=stack.pop()
   if node in seen:raise ValueError('cycle')
   seen.add(node);order.append(node);stack.extend(self.graph.edges[e].sink for e in reversed(children[node]))
  if seen!=nodes:raise ValueError('disconnected or cyclic union')
  downstream={}
  for node in reversed(order):
   total=self.nodes[node][1]
   for eid in children[node]:
    edge=self.graph.edges[eid];buffered,_,_,internal=self.switches[edge.switch_id];total+=internal
    if not buffered:total+=downstream[edge.sink]
   downstream[node]=total
  arrival={source:Fraction(0)};delay={}
  for node in order:
   delay[node]=arrival[node]+self.nodes[node][0]*downstream[node]/2
   for eid in children[node]:
    edge=self.graph.edges[eid];_,resistance,intrinsic,_=self.switches[edge.switch_id];arrival[edge.sink]=delay[node]+resistance*downstream[edge.sink]+intrinsic
  return {'downstream_capacitance':MappingProxyType(downstream),'delay_seconds':MappingProxyType(delay),'node_count':len(nodes),'edge_count':len(set(ids))}
