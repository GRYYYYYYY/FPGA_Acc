"""Exact electrical-only path memo, graph-epoch authenticated by caller batch."""
from collections import OrderedDict
from contextlib import contextmanager
from pathlib import Path
from buffered_rc_node_classes import read
from pre_route_endpoints import sha
class FractionPathMemo:
 def __init__(self,graph,digest,inventory,max_paths=10000):
  if type(max_paths) is not int or max_paths<1:raise ValueError('Positive cache limit required')
  self.graph=Path(graph);ids=inventory.node_classes;classes=inventory.classes;switches=inventory.electrical_switches;actual=inventory.digest
  if sha(graph)!=digest:raise ValueError('Graph epoch changed')
  if actual!=digest:raise ValueError('Wrong graph epoch')
  self.digest=digest;self.ids=tuple(ids);self.classes=tuple(classes);self.switches=dict(switches);self.limit=max_paths
  self.paths=OrderedDict();self.pairs={};self.stats=dict(hits=0,misses=0,evictions=0);self.active=False
 @contextmanager
 def batch(self):
  if self.active:raise ValueError('Nested or concurrent audit batch')
  if sha(self.graph)!=self.digest:raise ValueError('Graph epoch changed')
  self.active=True
  try:
   yield self
   if sha(self.graph)!=self.digest:raise ValueError('Graph changed during audit')
  finally:self.active=False
 def delay(self,path):
  if not self.active:raise ValueError('Authenticated audit batch required')
  key=tuple(tuple(x) for x in path)
  if not key or key[0][1] is not None:raise ValueError('Invalid source path')
  seen=set()
  for i,(node,switch) in enumerate(key):
   if type(node) is not int or not 0<=node<len(self.ids) or node in seen:raise ValueError('Invalid/cyclic path node')
   seen.add(node)
   if i and (type(switch) is not int or switch not in self.switches):raise ValueError('Invalid path switch')
  if key in self.paths:
   self.stats['hits']+=1;self.paths.move_to_end(key);return self.paths[key]
  self.stats['misses']+=1;r,c=self.classes[self.ids[key[0][0]]];value=r*c/2
  for node,switch in key[1:]:
   pair=(self.ids[node],switch)
   if pair not in self.pairs:
    r,c=self.classes[pair[0]];sr,td=self.switches[switch];self.pairs[pair]=(sr+r/2)*c+td
   value+=self.pairs[pair]
  self.paths[key]=value
  if len(self.paths)>self.limit:self.paths.popitem(last=False);self.stats['evictions']+=1
  return value
