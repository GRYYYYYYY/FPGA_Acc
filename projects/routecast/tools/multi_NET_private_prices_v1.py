"""Sparse private occupancy synchronization and a frozen group objective price."""
from collections import Counter
from types import MappingProxyType

def sync(context,target,touched):
 if context.active is not None:raise RuntimeError('active private price ticket')
 updates={}
 for node in touched:
  value=target.get(node,0);context.check_count(node,value)
  if value!=context.ledger.get(node,0):updates[node]=value
 prices={n:context.price(n,v) for n,v in updates.items()};context.search.patch_prices(prices)
 for node,value in updates.items():
  if value:context.ledger[node]=value
  else:context.ledger.pop(node,None)
 return len(updates)

class GroupPrices:
 def __init__(self,context,ledger,removed_owner_counts):
  self.base=context.base;self.history=context.history;self.caps=context.caps;self.spans=context.spans;self.weight=context.weight;self.ledger=ledger;self.removed=MappingProxyType(dict(removed_owner_counts))
  for n,c in self.removed.items():
   if type(c) is not int or c<1 or ledger.get(n,0)<c:raise ValueError('missing group owners')
 def get(self,node,default=0):
  other=self.ledger.get(node,0)-self.removed.get(node,0)
  return self.base[node]*(1+self.history[node])*(1+max(0,other-self.caps[node]+1))+self.weight*self.spans[node]

def groups(dirty,owned,ledger,capacities):
 overused={n for n,c in ledger.items() if c>capacities[n]};owners={n:set() for n in overused}
 for net,nodes in owned.items():
  for n in nodes&overused:owners[n].add(net)
 used=set();answer=[]
 for net in sorted(dirty):
  if net in used:continue
  neighbors=set()
  for n in owned[net]&overused:neighbors.update(owners[n])
  neighbors-=used|{net};group=tuple(sorted((net,min(neighbors)))) if neighbors else (net,);answer.append(group);used.update(group)
 return answer
