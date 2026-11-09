"""Cached owner snapshots with explicit rational present factor per round."""
from fractions import Fraction
from cached_multiplicative_occupancy_context_v1 import Context as OriginalContext
from pressure_scaled_node_cost_v1 import cost
class Context(OriginalContext):
 def __init__(self,*args,**kwargs):
  self.present_factor=Fraction(1);super().__init__(*args,**kwargs)
 def price(self,node,count):
  return cost(self.base[node],self.history[node],count,self.caps[node],self.present_factor,False,self.weight*self.spans[node])-self.base[node]
