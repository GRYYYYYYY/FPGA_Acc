"""Ordinary bounded FIFO memoization of a pure congestion scalar, never transactions."""
import time
from collections import Counter
CAPACITY=131072
class Memo:
 def __init__(self):
  self.table={};self.version=0;self.stats=Counter();self.epochs=[];self.started=time.monotonic();self.seen=set();self.roles=Counter()
 def reset(self):
  self.epochs.append({'version':self.version,'lifetime_s':time.monotonic()-self.started,'distinct_keys':len(self.seen),'calls':sum(self.roles.values()),'roles':dict(self.roles)})
  t=time.perf_counter();self.table.clear();self.seen.clear();self.roles.clear();self.version+=1;self.started=time.monotonic();self.stats['invalidation_s']+=time.perf_counter()-t;self.stats['invalidations']+=1
 def get(self,engine,source,sink,positions,original,diagnostic=False):
  a,b=positions[source],positions[sink];key=(self.version,a[0],a[1],b[0],b[1]);self.stats['queries']+=1
  if diagnostic:
   self.seen.add(key);self.roles['before' if positions is engine.positions else 'candidate']+=1
  value=self.table.get(key)
  if value is not None:self.stats['hits']+=1;return value
  self.stats['misses']+=1;value=original(engine,source,sink,positions)
  if len(self.table)>=CAPACITY:self.table.pop(next(iter(self.table)));self.stats['evictions']+=1
  self.table[key]=value;self.stats['peak_entries']=max(self.stats['peak_entries'],len(self.table));return value
