"""Full-map validated replacement with changed-cell writes only; serial owner."""
from native_capacity_rc_search import NativeCapacityRC

class NativeCapacityRCDiffDemand(NativeCapacityRC):
 def __init__(self,rc):
  super().__init__(rc);self.publication_calls=0;self.publication_writes=0
 def set_other(self,other):
  staged={}
  for node,value in other.items():
   if type(node) is not int or not 0<=node<self.n or type(value) is not int or not 0<=value<(1<<64):raise ValueError('invalid otherNET demand')
   if value:staged[node]=value
  previous=set(staged)
  changes=[(node,0) for node in self.previous if node not in staged]
  changes.extend((node,value) for node,value in staged.items() if self.other[node]!=value)
  # Iterator/validation and allocation have completed before publication.
  for node,value in changes:self.other[node]=value
  self.previous=previous;self.publication_calls+=1;self.publication_writes+=len(changes)
