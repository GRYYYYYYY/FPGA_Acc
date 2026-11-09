"""Single-owner serial endpoint/score publication; no cross-thread/crash guarantee.

Opaque prepare tickets only: callers cannot supply incomplete score patches.
Published endpoint caches are never mutated; readers retain captured versions.
"""
from collections import namedtuple
from copy import copy
from incremental_IPIN_feature_cache_v1 import Cache,pages,lookup,patched
State=namedtuple('State','endpoints scores')

class View:
 def __init__(self,state):self.__state=state
 @property
 def generation(self):return self.__state.endpoints.generation
 def query(self,cid):return self.__state.endpoints.query(cid)
 def class_feature(self,sink):return self.__state.endpoints.class_feature(sink)
 def score(self,node):
  value=lookup(self.__state.scores,node)
  if value is None:raise ValueError('unknown IPIN')
  return value
 def endpoint_snapshot(self):return self.__state.endpoints.snapshot()

class Joint:
 def __init__(self,graph_epoch,groups,valid_sources,connections):
  self._groups={s:tuple(nodes) for s,nodes in groups.items()}
  seen=set()
  for nodes in self._groups.values():
   if not nodes:raise ValueError('empty group')
   for n in nodes:
    if type(n) is not int or n<0 or n in seen:raise ValueError('duplicate/invalid IPIN')
    seen.add(n)
  cache=Cache(graph_epoch,{s:len(ns) for s,ns in self._groups.items()},valid_sources,connections)
  scores={}
  for s,nodes in self._groups.items():
   value=tuple(float(x) for x in cache.class_feature(s)[1:])
   for n in nodes:scores[n]=value
  self._state=State(cache,pages(scores));self._pending={}
 def view(self):return View(self._state)
 def prepare(self,graph_epoch,generation,edits):
  before=self._state
  # Shallow scratch shares only immutable-by-convention published COW pages.
  scratch=copy(before.endpoints);scratch._pending={}
  receipt=scratch.commit(scratch.prepare(graph_epoch,generation,edits))
  updates={}
  for s in receipt['changed_count_classes']:
   value=tuple(float(x) for x in scratch.class_feature(s)[1:])
   for n in self._groups[s]:updates[n]=value
  scores,copied,entries=patched(before.scores,updates)
  after=State(scratch,scores)
  result=dict(receipt,score_updates=len(updates),score_copied_shards=copied,score_copied_entries=entries)
  token=object();self._pending[token]=(before,after,result);return token
 def commit(self,token):
  if token not in self._pending:raise ValueError('foreign/consumed ticket')
  before,after,result=self._pending[token]
  if self._state is not before:
   del self._pending[token];raise ValueError('stale ticket')
  receipt=dict(result)
  self._state=after
  del self._pending[token]
  return receipt
