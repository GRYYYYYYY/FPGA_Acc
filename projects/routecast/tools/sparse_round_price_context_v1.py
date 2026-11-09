"""Persistent round-price component; graph/RC lifetime remains caller-owned.

An epoch token binds the caller's immutable inputs. It is not a file authenticator.
Serial only, with the same interruption guarantees as Store.patch_prices.
"""
from collections import Counter
from cached_multiplicative_occupancy_context_v1 import Context as DenseContext
from multiplicative_net_congestion_v1 import cost

class Context(DenseContext):
 def __init__(self,*args,epoch,**kwargs):
  if type(epoch) is not str or not epoch:raise ValueError('epoch token required')
  super().__init__(*args,**kwargs)
  self.epoch=epoch
 def start_round(self,history,weight,ledger):
  if self.ready:raise RuntimeError('use explicit history increments after initialization')
  super().start_round(history,weight,ledger)
  self.history=list(self.history)
  self.max_history=max(self.history,default=0)
  self.max_base=max(self.base,default=0)
  self.max_span=max(self.spans,default=0)
 def advance_round(self,increments,weight,ledger,*,epoch):
  if not self.ready or self.active is not None or self.search.closed:raise RuntimeError('invalid round lifecycle')
  if epoch!=self.epoch:raise ValueError('stale immutable epoch')
  if type(weight) is not int or weight!=self.weight:raise ValueError('weight changed; rebuild context')
  counts=dict(ledger)
  for n,v in counts.items():self.check_count(n,v)
  if Counter({n:v for n,v in counts.items() if v})!=self.ledger:raise ValueError('owner ledger drift')
  changes=dict(increments)
  histories={}
  for n,v in changes.items():
   self.check_node(n)
   if type(v) is not int or v<0:raise ValueError('invalid history increment')
   if v:histories[n]=self.history[n]+v
  maximum=max([self.max_history,*histories.values()])
  ceiling=self.max_base*(1+maximum)*(self.limit+1)+weight*self.max_span
  if not 0<=ceiling<2**128:raise ValueError('price ceiling overflow')
  prices={n:cost(self.base[n],h,self.ledger.get(n,0),self.caps[n],False,weight*self.spans[n])-self.base[n] for n,h in histories.items()}
  # Validation and allocation above precede serial mutation; no concurrent use.
  self.search.price_ceiling=ceiling
  self.search.patch_prices(prices)
  for n,h in histories.items():self.history[n]=h
  self.max_history=maximum
  return len(prices)
