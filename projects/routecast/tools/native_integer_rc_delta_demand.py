"""Serial versioned absolute demand updates; caller supplies complete delta.

Storage and previous-node set copying remain O(active nodes). No concurrent
publication guarantee; version checks reject stale callers, not missing updates.
"""
from native_integer_rc_sparse_trace import NativeIntegerRCSparseTrace

class NativeIntegerRCDeltaDemand(NativeIntegerRCSparseTrace):
 def __init__(self,rc):
  super().__init__(rc);self.demand_epoch=0
 def set_other(self,other):
  super().set_other(other);self.demand_epoch+=1
 def apply_other(self,expected_epoch,updates):
  if type(expected_epoch) is not int or expected_epoch!=self.demand_epoch:raise ValueError('stale demand epoch')
  staged={}
  for node,value in updates:
   if type(node) is not int or not 0<=node<self.n or type(value) is not int or not 0<=value<(1<<64) or node in staged:raise ValueError('invalid demand delta')
   staged[node]=value
  previous=self.previous.copy()
  for node,value in staged.items():
   if value:previous.add(node)
   else:previous.discard(node)
  next_epoch=self.demand_epoch+1
  for node,value in staged.items():self.other[node]=value
  self.previous=previous;self.demand_epoch=next_epoch
  return next_epoch
