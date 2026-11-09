"""Keep exact raw budgets; add structural cost to the existing union objective."""
from resident_actual_old_fallback_undo_adapter_v2 import fallback as Original

def fallback(fields,rc,slots,queries,old_records,parents,settled,prices,weight,node_base,max_states=10000):
 if type(weight) is not int or weight<0 or len(node_base)!=len(fields['capacities']):raise ValueError('structural cost domain')
 class ObjectivePrice:
  def get(self,node,default=0):
   base=node_base[node];price=prices.get(node,0)
   if type(base) is not int or base<0 or type(price) is not int or price<0:raise ValueError('negative or invalid objective component')
   return base+weight*price
 # The original adapter stores RC increments separately from objective penalties.
 # Weight one allows positive structural costs even when congestion weight is zero.
 return Original(fields,rc,slots,queries,old_records,parents,settled,ObjectivePrice(),1,max_states)
