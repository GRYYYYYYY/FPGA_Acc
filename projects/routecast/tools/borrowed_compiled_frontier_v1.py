"""Read-only geometry probe over the initializer's existing compiled Tree owner.

Actual compiled search seeds are every arrival key, including IPIN/SINK. A
separate projection excludes these terminal kinds. No graph/NET index or native
search workspace is created; each capture still scans the existing tree keys.
"""
from retained_tree_frontier_state_v3 import GraphContext
from retained_tree_frontier_state_v1 import EXPAND

class Probe:
 def __init__(self,graph,context):
  if type(context) is not GraphContext or graph.closed or len(context.geometry)!=graph.n or min(context.geometry,default=-1)!=0 or max(context.geometry,default=-1)!=graph.n-1:raise ValueError('live graph and complete validated geometry required')
  self.graph=graph;self.context=context
 def capture(self,tree,target):
  g=self.graph;geo=self.context.geometry
  if g.closed or tree.graph is not g or tree.offsets is not g.offsets or tree.dest is not g.dest or tree.inc is not g.inc or tree.initial is not g.initial:raise ValueError('foreign/closed tree owner')
  if type(target) is not int or target not in geo or geo[target][0]!='SINK' or geo[tree.source][0]!='SOURCE' or tree.source not in tree.arrival:raise ValueError('tree source/target')
  sink=geo[target];actual=projected=actual_same=projected_same=0;actual_min=projected_min=None
  for node in tree.arrival:
   if type(node) is not int or node not in geo:raise ValueError('tree node domain')
   a=geo[node];actual+=1;expand=a[0] in EXPAND;projected+=expand
   if a[5]!=sink[5]:continue
   distance=max(0,a[1]-sink[2],sink[1]-a[2])+max(0,a[3]-sink[4],sink[3]-a[4]);actual_same+=1;actual_min=distance if actual_min is None else min(actual_min,distance)
   if expand:projected_same+=1;projected_min=distance if projected_min is None else min(projected_min,distance)
  return dict(graph_epoch=self.context.epoch,source=tree.source,target=target,actual_seed_nodes=actual,actual_same_layer_nodes=actual_same,actual_min_tile_L1=actual_min,projected_expandable_nodes=projected,projected_same_layer_nodes=projected_same,projected_min_tile_L1=projected_min)
