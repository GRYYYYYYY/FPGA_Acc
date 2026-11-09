"""Serial sparse price patches under a prevalidated fixed cost ceiling."""
from lazy_compact_wide_structural_objective_search_v1 import Search as Base

class Search(Base):
 def prepare(self,prices,weight,*,structural=True,price_ceiling=None):
  n=len(self.base);ceiling=max((prices.get(u,0) for u in range(n)),default=0) if price_ceiling is None else price_ceiling
  if type(ceiling) is not int or not 0<=ceiling<2**120:raise ValueError('invalid price ceiling')
  values=tuple(prices.get(u,0) for u in range(n))
  if any(type(v) is not int or not 0<=v<=ceiling for v in values):raise ValueError('price exceeds ceiling')
  if type(weight) is not int or not 0<=weight<2**120:raise ValueError('invalid weight')
  inc=self.objective_inc if structural else self.raw_inc
  if 2*n*(max(inc,default=0)+weight*ceiling)+max(self.initial,default=0)>=2**120:raise ValueError('ceiling cost envelope exceeded')
  super().prepare(dict(enumerate(values)),weight,structural=structural)
  self.prices=list(self.prices);self.price_ceiling=ceiling;self.price_epoch=0
 def patch_prices(self,changes):
  if self.closed or not self.prepared:raise RuntimeError('closed or unprepared price context')
  updates=dict(changes)
  for node,value in updates.items():
   if type(node) is not int or not 0<=node<len(self.base) or type(value) is not int or not 0<=value<=self.price_ceiling:raise ValueError('invalid sparse price patch')
  backend=self.backends[int(self.structural)]
  # All values are validated before touching either owned backend buffer.
  # Calls are serial; no concurrent-search or interrupt atomicity guarantee.
  for node,value in updates.items():
   backend.forward.price[node]=value;backend.bidirectional.price[node]=value;self.prices[node]=value
  if updates:self.price_epoch+=1
