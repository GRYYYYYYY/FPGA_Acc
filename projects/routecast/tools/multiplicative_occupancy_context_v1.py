"""Existing owner transaction mechanics with separate history/span multiplicative pricing."""
from collections import Counter
from present_occupancy_context_v1 import Context as OriginalContext
from multiplicative_net_congestion_v1 import cost
class Context(OriginalContext):
 def __init__(self,search,capacities,node_base,max_owners,span_prices):
  super().__init__(search,capacities,node_base,max_owners)
  self.spans=tuple(span_prices.get(n,0) for n in range(len(self.caps)))
  if any(type(v) is not int or v<0 for v in self.spans):raise ValueError('span domain')
 def price(self,node,count):
  return cost(self.base[node],self.history[node],count,self.caps[node],False,self.weight*self.spans[node])-self.base[node]
 def start_round(self,history,weight,ledger):
  if self.active is not None:raise RuntimeError('active transaction at round change')
  if type(weight) is not int or not 0<=weight<2**64:raise ValueError('weight')
  h=tuple(history.get(n,0)-self.spans[n] for n in range(len(self.caps)))
  if any(type(v) is not int or v<0 for v in h):raise ValueError('history missing static span or invalid count')
  counts=dict(ledger)
  for n,v in counts.items():self.check_count(n,v)
  self.history=h;self.weight=weight
  ceiling=max(self.base,default=0)*(1+max(h,default=0))*(self.limit+1)+weight*max(self.spans,default=0)
  prices={n:self.price(n,counts.get(n,0)) for n in range(len(h))}
  self.search.prepare(prices,1,structural=True,price_ceiling=ceiling)
  self.ledger=Counter({n:v for n,v in counts.items() if v});self.ready=True
