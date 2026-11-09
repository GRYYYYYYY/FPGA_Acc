"""Serial own-NET exclusion transitions; caller supplies all occupancy dirties.

The initial synchronization scans active occupancy and scratch once. Subsequent
transitions inspect previous/current excluded unions and changed occupancy only.
The native buffer retains its existing active-set-copy cost.
"""
class LocalOtherDemand:
 def __init__(self,native):
  self.native=native;self.values={n:int(native.other[n]) for n in native.previous}
  self.excluded=None
 def transition(self,occupancy,excluded,dirty=()):
  excluded=frozenset(excluded)
  nodes=(self.values.keys()|occupancy.keys()) if self.excluded is None else self.excluded|excluded|set(dirty)
  updates=[]
  for n in nodes:
   value=occupancy.get(n,0)-int(n in excluded)
   if value<0:raise ValueError('excluded NET absent from occupancy')
   if value!=self.values.get(n,0):updates.append((n,value))
  self.native.apply_other(self.native.demand_epoch,updates)
  for n,value in updates:
   if value:self.values[n]=value
   else:self.values.pop(n,None)
  self.excluded=excluded
  return len(updates),len(nodes)
