"""Serial validated absolute deltas and caller-owned occupancy dirty transitions."""
import hashlib,time
from native_capacity_rc_diff_demand import NativeCapacityRCDiffDemand

class CapacityAbsoluteDemand(NativeCapacityRCDiffDemand):
 def __init__(self,rc):
  super().__init__(rc);self.demand_epoch=self.delta_calls=self.delta_writes=0
 def set_other(self,other):
  super().set_other(other);self.demand_epoch+=1
 def apply_other(self,expected_epoch,updates):
  if type(expected_epoch) is not int or expected_epoch!=self.demand_epoch:raise ValueError('stale demand epoch')
  staged={}
  for node,value in updates:
   if type(node) is not int or not 0<=node<self.n or type(value) is not int or not 0<=value<(1<<64) or node in staged:raise ValueError('invalid absolute delta')
   staged[node]=value
  previous=self.previous.copy()
  for node,value in staged.items():
   if value:previous.add(node)
   else:previous.discard(node)
  epoch=self.demand_epoch+1
  for node,value in staged.items():self.other[node]=value
  self.previous=previous;self.demand_epoch=epoch;self.delta_calls+=1;self.delta_writes+=len(staged)
  return epoch

class CapacityLocalDemand:
 def __init__(self,native):
  self.native=native;self.epoch=native.demand_epoch;self.values={node:int(native.other[node]) for node in native.previous};self.excluded=None
 def transition(self,occupancy,excluded,dirty=()):
  if self.epoch!=self.native.demand_epoch:raise ValueError('external demand change requires resynchronization')
  owner=set();changed=set()
  for target,items in [(owner,excluded),(changed,dirty)]:
   for node in items:
    if type(node) is not int or not 0<=node<self.native.n:raise ValueError('invalid transition node')
    target.add(node)
  nodes=(self.values.keys()|occupancy.keys()|owner) if self.excluded is None else self.excluded|owner|changed
  updates=[]
  for node in nodes:
   if type(node) is not int or not 0<=node<self.native.n:raise ValueError('invalid occupancy node')
   count=occupancy.get(node,0)
   if type(count) is not int or not 0<=count<(1<<64):raise ValueError('invalid occupancy')
   value=count-int(node in owner)
   if value<0:raise ValueError('excluded owner absent from occupancy')
   if value!=self.values.get(node,0):updates.append((node,value))
  self.epoch=self.native.apply_other(self.epoch,updates)
  for node,value in updates:
   if value:self.values[node]=value
   else:self.values.pop(node,None)
  self.excluded=frozenset(owner)
  return len(updates),len(nodes)

def resident_query(ctx,local,ledger,owner,dirty,source,sink,budget,max_labels=10000):
 tick=time.perf_counter();writes,visited=local.transition(ledger,owner,dirty);dirty.clear();ctx.demand_stats['calls']+=1;ctx.demand_stats['writes']+=writes;ctx.demand_stats['visited']+=visited;ctx.demand_stats['seconds']+=time.perf_counter()-tick
 ctx.demand_journal.append(dict(source=source,sink=sink,mode='resident',epoch=ctx.native.demand_epoch,digest=hashlib.sha256(ctx.native.other.tobytes()).hexdigest()))
 return ctx.native.query(source,sink,budget,max_labels=max_labels)
