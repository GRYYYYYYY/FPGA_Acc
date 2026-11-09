"""Serial whole-NET virtual release and sparse prospective occupancy prices."""
from collections import Counter

class PriceView:
 def __init__(self,context,ticket):self.context=context;self.ticket=ticket
 def get(self,node,default=0):
  c=self.context
  if c.active!=self.ticket or c.search.closed:raise RuntimeError('stale occupancy snapshot')
  c.check_node(node)
  return c.price(node,c.ledger.get(node,0)-(node in c.old))

class Context:
 def __init__(self,search,capacities,node_base,max_owners):
  self.search=search;self.caps=tuple(capacities);self.base=tuple(node_base);self.limit=max_owners
  if type(max_owners) is not int or max_owners<1 or self.caps!=search.fields['capacities'] or self.base!=search.base:raise ValueError('context domain mismatch')
  if any(type(v) is not int or v<0 for v in self.caps):raise ValueError('invalid capacities')
  self.active=None;self.ticket=0;self.ready=False
 def check_node(self,node):
  if type(node) is not int or not 0<=node<len(self.caps):raise ValueError('invalid node')
 def check_count(self,node,count):
  self.check_node(node)
  if type(count) is not int or not 0<=count<=self.limit or count and not self.caps[node]:raise ValueError('invalid occupancy')
 def price(self,node,count):
  return self.weight*self.history[node]+self.base[node]*max(0,count-self.caps[node]+1)
 def start_round(self,history,weight,ledger):
  if self.active is not None:raise RuntimeError('active transaction at round change')
  h=tuple(history.get(n,0) for n in range(len(self.caps)))
  if type(weight) is not int or not 0<=weight<2**64 or any(type(v) is not int or v<0 for v in h):raise ValueError('invalid history cost')
  counts={n:v for n,v in ledger.items()}
  for n,v in counts.items():self.check_count(n,v)
  ceiling=weight*max(h,default=0)+max(self.base,default=0)*(self.limit+1)
  prices={n:weight*h[n]+self.base[n]*max(0,counts.get(n,0)-self.caps[n]+1) for n in range(len(h))}
  self.search.prepare(prices,1,structural=True,price_ceiling=ceiling)
  self.history=h;self.weight=weight;self.ledger=Counter({n:v for n,v in counts.items() if v});self.ready=True
 def begin(self,old_owned):
  if not self.ready or self.active is not None:raise RuntimeError('unready or nested transaction')
  old=frozenset(old_owned)
  for n in old:
   self.check_node(n)
   if self.ledger.get(n,0)<1:raise ValueError('old owner not present')
  changes={n:self.price(n,self.ledger[n]-1) for n in old}
  self.search.patch_prices({n:v for n,v in changes.items() if self.search.prices[n]!=v})
  self.ticket+=1;self.active=self.ticket;self.old=old
  return PriceView(self,self.ticket)
 def finish(self,updates=None):
  if self.active is None:raise RuntimeError('no active transaction')
  changes={} if updates is None else dict(updates)
  for n,v in changes.items():
   self.check_count(n,v);delta=v-self.ledger.get(n,0)
   if delta not in {-1,0,1} or delta==-1 and n not in self.old or delta==1 and n in self.old:raise ValueError('not a single NET owner replacement')
  touched=self.old|changes.keys()
  prices={n:self.price(n,changes.get(n,self.ledger.get(n,0))) for n in touched}
  self.search.patch_prices({n:v for n,v in prices.items() if self.search.prices[n]!=v})
  for n,v in changes.items():
   if v:self.ledger[n]=v
   else:self.ledger.pop(n,None)
  self.active=None;self.old=frozenset()
