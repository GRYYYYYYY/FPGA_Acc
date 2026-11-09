"""Exact local score for replacement of ONE net union with fixed endpoints.

Caller supplies a previously verified global score and verified external
unique-net demand excluding this net. No path/tree/pin legality is inferred.
Only affected nodes are read from the external context; endpoint HPWL is fixed.
"""
from types import MappingProxyType

class LocalChannelScores:
 def __init__(self,graph):
  self.graph=graph;spans={}
  for n,node in graph.nodes.items():
   if node.type in {'CHANX','CHANY'}:
    loc=dict(node.location);spans[n]=max(int(loc['xhigh'])-int(loc['xlow']),int(loc['yhigh'])-int(loc['ylow']))+1
  self.spans=MappingProxyType(spans)
 def replace_net(self,current_score,old_nodes,new_nodes,external_demand):
  fields={'channel_net_span_sum','predicted_channel_overuse_units','net_bbox_hpwl'}
  if set(current_score)!=fields or any(type(current_score[k]) is not int or current_score[k]<0 for k in fields):raise ValueError('invalid verified baseline score')
  old=frozenset(old_nodes);new=frozenset(new_nodes)
  if any(type(n) is not int or n not in self.graph.nodes or self.graph.nodes[n].capacity<=0 for n in old|new):raise ValueError('invalid or disabled net node')
  length=current_score['channel_net_span_sum'];overuse=current_score['predicted_channel_overuse_units']
  for n in old^new:
   if n not in self.spans:continue
   outside=external_demand.get(n,0)
   if type(outside) is not int or outside<0:raise ValueError('invalid external unique-net demand')
   before=outside+int(n in old);after=outside+int(n in new);cap=self.graph.nodes[n].capacity
   length+=(after-before)*self.spans[n];overuse+=max(0,after-cap)-max(0,before-cap)
  if length<0 or overuse<0:raise ValueError('baseline inconsistent with replacement delta')
  return {'channel_net_span_sum':length,'predicted_channel_overuse_units':overuse,'net_bbox_hpwl':current_score['net_bbox_hpwl']}
