"""Exact additive lattice path evaluation with physical-edge direct indexing.

Retains original rational model via base; initial/increments were encoded by
that model. No owner, path-result, native STA or loaded branch capacitance cache.
"""
from array import array
class IndexedIntegerRC:
 def __init__(self,base,fields,initial,inventory):
  self.base=base;self.scale=base.scale;self.increments=base.increments;self.fields=fields;self.initial_values=tuple(initial);self.edges=inventory.edges
  m=len(fields['edge_ids']);self.slots=array('Q',[m])*m;assert len(self.edges)==m and len(self.increments)==m
  for u in range(len(initial)):
   for s in range(fields['row_offsets'][u],fields['row_offsets'][u+1]):
    eid=fields['edge_ids'][s]
    if eid>=m or self.slots[eid]!=m or self.edges[eid]!=(u,fields['dest_ranks'][s],fields['switch_ids'][s]):raise ValueError('physical edge index identity')
    self.slots[eid]=s
  if any(s==m for s in self.slots):raise ValueError('incomplete physical edge index')
 def __getattr__(self,name):return getattr(self.base,name)
 def initial(self,node):
  if type(node) is not int or not 0<=node<len(self.initial_values):raise ValueError('invalid raw node')
  return self.initial_values[node]
 def path(self,source,sink,edge_ids):
  value=self.initial(source);self.initial(sink);current=source;seen={source}
  for eid in edge_ids:
   if type(eid) is not int or not 0<=eid<len(self.edges):raise ValueError('invalid raw edge ID')
   u,v,sw=self.edges[eid]
   if u!=current:raise ValueError('discontinuous raw edge')
   if v in seen:raise ValueError('cyclic path')
   seen.add(v);current=v;value+=self.increments[self.slots[eid]]
  if current!=sink:raise ValueError('wrong terminal')
  return value
