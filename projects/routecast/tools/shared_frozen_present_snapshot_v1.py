"""One immutable full resource snapshot, query-local old-owner views."""
from scaled_frozen_present_prices_v1 import Prices
class Snapshot:
 def __init__(self,bases,acc,occupancy,capacities,present,static=None):
  self._prices=Prices(bases,acc,occupancy,capacities,(),present,static)
 def for_owner(self,owned):
  p=self._prices;owner=frozenset(owned)
  if any(type(n) is not int or not 0<=n<len(p.base) or p.occ[n]==0 for n in owner):raise ValueError('old owner domain')
  view=Prices.__new__(Prices)
  for key in ('base','acc','occ','cap','static','denominator','numerator'):setattr(view,key,getattr(p,key))
  view.owned=owner
  return view
