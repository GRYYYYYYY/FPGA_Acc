"""Exact sparse price memoization scoped to one serial NET transaction ticket."""
from multiplicative_occupancy_context_v1 import Context as OriginalContext
from present_occupancy_context_v1 import PriceView as OriginalView

class PriceView(OriginalView):
 def __init__(self,context,ticket):
  super().__init__(context,ticket);self._cache={}
 def get(self,node,default=0):
  c=self.context
  if c.active!=self.ticket or c.search.closed:raise RuntimeError('stale occupancy snapshot')
  c.check_node(node)
  value=self._cache.get(node)
  if value is None:
   value=c.price(node,c.ledger.get(node,0)-(node in c.old));self._cache[node]=value
  return value

class Context(OriginalContext):
 def begin(self,old_owned):
  view=super().begin(old_owned)
  return PriceView(view.context,view.ticket)
