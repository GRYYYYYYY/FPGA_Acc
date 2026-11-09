"""Single-owner serial full-domain typed-prior state for admitted node projections.

One publication joins endpoints, NET ownership and two score fields. This is not
physical path/RC admission, threading synchronization, or durable storage.
"""
from collections import namedtuple
from copy import copy
from fractions import Fraction
from incremental_IPIN_feature_cache_v1 import Cache as Endpoints,pages,lookup,patched
from incremental_NET_group_ownership_v1 import Cache as Ownership

State=namedtuple('State','generation endpoints ownership scores')
EMPTY=(Fraction(0),Fraction(1),Fraction(0))

def fork(cache):
 result=copy(cache);result._pending={};return result

def advance(cache,epoch,generation,edits):
 result=fork(cache)
 if edits:receipt=result.commit(result.prepare(epoch,generation,edits))
 else:
  result._state=result._state._replace(generation=generation+1);receipt={}
 return result,receipt

class View:
 def __init__(self,state):self.__state=state
 @property
 def generation(self):return self.__state.generation
 @property
 def component_generations(self):return self.__state.endpoints.generation,self.__state.ownership.generation
 def score(self,node):
  value=lookup(self.__state.scores,node)
  if value is None:raise ValueError('unknown positive RR')
  return value
 def query(self,cid):
  row=self.__state.endpoints.query(cid);value=lookup(self.__state.ownership._state.queries,cid)
  return dict(row,nodes=sorted(value[1]))
 def endpoint_snapshot(self):return self.__state.endpoints.snapshot()
 def ownership_snapshot(self):return self.__state.ownership.snapshot()

class Joint:
 def __init__(self,graph_epoch,eligible_groups,ipin_sink_groups,valid_sources,capacities,records):
  self._epoch=graph_epoch;self._capacities=dict(capacities);self._sources=frozenset(valid_sources)
  if any(type(n) is not int or n<0 or type(c) is not int or c<1 for n,c in self._capacities.items()):raise ValueError('positive capacity domain')
  self._groups={gid:tuple(ns) for gid,ns in eligible_groups.items()};self._group_of={}
  for gid,nodes in self._groups.items():
   if type(gid) is not int or gid<0 or not nodes:raise ValueError('group')
   for n in nodes:
    if n in self._group_of or n not in capacities or capacities[n]!=1:raise ValueError('unit group partition')
    self._group_of[n]=gid
  self._ipin_sinks=dict(ipin_sink_groups)
  if len(set(self._ipin_sinks.values()))!=len(self._ipin_sinks):raise ValueError('duplicate sink group')
  if any(s not in capacities or gid not in self._groups for s,gid in self._ipin_sinks.items()):raise ValueError('IPIN sink context')
  self._ipin_nodes={n:s for s,gid in self._ipin_sinks.items() for n in self._groups[gid]}
  if not self._sources<=self._capacities.keys() or self._sources & self._ipin_sinks.keys():raise ValueError('source domain')
  if (self._sources|self._ipin_sinks.keys()) & self._group_of.keys():raise ValueError('fixed endpoint grouped')
  self._fallback={};gid=max(self._groups,default=-1)+1
  for n in sorted(self._capacities.keys()-self._group_of.keys()):
   self._fallback[gid]=n;self._groups[gid]=(n,);self._group_of[n]=gid;gid+=1
  normalized=[self._normalize(r) for r in records]
  endpoints=Endpoints(graph_epoch,{s:len(self._groups[g]) for s,g in self._ipin_sinks.items()},self._sources,[self._endpoint(r) for r in normalized])
  ownership=Ownership(graph_epoch,self._groups,[self._projection(r) for r in normalized]);self._check_IPIN(endpoints,ownership,self._ipin_sinks)
  scores={}
  for gid,nodes in self._groups.items():
   value=self._score(ownership,gid)
   for n in nodes:scores[n]=value
  self._state=State(0,endpoints,ownership,pages(scores));self._pending={}
 def _normalize(self,row):
  if set(row)!={'connection_id','net_id','source','sink','nodes'}:raise ValueError('full query schema')
  if any(type(row[k]) is not int or row[k]<0 for k in ['connection_id','net_id','source','sink']):raise ValueError('identity')
  if row['source'] not in self._sources or row['sink'] not in self._ipin_sinks:raise ValueError('endpoint domain')
  if not isinstance(row['nodes'],(list,tuple,set,frozenset)) or any(type(n) is not int or n not in self._capacities for n in row['nodes']):raise ValueError('node projection')
  nodes=frozenset(row['nodes']);source=row['source'];sink=row['sink']
  if nodes & self._sources!={source} or nodes & self._ipin_sinks.keys()!={sink}:raise ValueError('projection endpoint mismatch')
  pins=nodes & self._ipin_nodes.keys()
  if len(pins)!=1 or any(self._ipin_nodes[n]!=sink for n in pins):raise ValueError('terminal IPIN projection mismatch')
  return dict(row,nodes=nodes)
 @staticmethod
 def _endpoint(r):return {k:r[k] for k in ['connection_id','net_id','source','sink']}
 @staticmethod
 def _projection(r):return {k:r[k] for k in ['connection_id','net_id','nodes']}
 def _score(self,ownership,gid):
  feature=lookup(ownership._state.features,gid,EMPTY)
  if gid in self._fallback:
   n=self._fallback[gid];capacity=self._capacities[n];value=float(max(Fraction(0),feature[0]-capacity)/capacity);return value,value
  return float(feature[0]),float(feature[2])
 def _check_IPIN(self,endpoints,ownership,sinks):
  for sink in sinks:
   gid=self._ipin_sinks[sink];f=lookup(ownership._state.features,gid,EMPTY);q,mean,risk=endpoints.class_feature(sink)
   if (f[0],f[2])!=(mean,risk):raise ValueError('IPIN endpoint/ownership disagreement')
 def view(self):return View(self._state)
 def prepare(self,graph_epoch,generation,edits):
  before=self._state
  if graph_epoch!=self._epoch or type(generation) is not int or generation!=before.generation:raise ValueError('graph/generation mismatch')
  if not edits:raise ValueError('empty batch')
  endpoint_edits=[];projection_edits=[];seen=set();sinks=set()
  for edit in edits:
   if set(edit)!={'old','new'}:raise ValueError('edit schema')
   old,new=self._normalize(edit['old']),self._normalize(edit['new']);cid=old['connection_id']
   if cid in seen or cid!=new['connection_id'] or old['net_id']!=new['net_id']:raise ValueError('fixed CID/NET domain')
   seen.add(cid)
   if before.endpoints.query(cid)!=self._endpoint(old) or lookup(before.ownership._state.queries,cid)!=(old['net_id'],old['nodes']):raise ValueError('stale full descriptor')
   if old==new:raise ValueError('no-op')
   if self._endpoint(old)!=self._endpoint(new):endpoint_edits.append(dict(old=self._endpoint(old),new=self._endpoint(new)))
   if old['nodes']!=new['nodes']:projection_edits.append(dict(old=self._projection(old),new=self._projection(new)))
   sinks.update([old['sink'],new['sink']])
  endpoints,er=advance(before.endpoints,graph_epoch,generation,endpoint_edits)
  ownership,pr=advance(before.ownership,graph_epoch,generation,projection_edits)
  self._check_IPIN(endpoints,ownership,sinks)
  updates={}
  for gid in pr.get('touched_histogram_groups',()):
   value=self._score(ownership,gid)
   for n in self._groups[gid]:updates[n]=value
  scores,np,ne=patched(before.scores,updates);after=State(generation+1,endpoints,ownership,scores)
  receipt=dict(generation=after.generation,query_updates=len(seen),endpoint_updates=len(endpoint_edits),projection_updates=len(projection_edits),score_updates=len(updates),score_copied_shards=np,score_copied_entries=ne,endpoint_receipt=er,ownership_receipt=pr)
  token=object();self._pending[token]=(before,after,receipt);return token
 def commit(self,token):
  if token not in self._pending:raise ValueError('foreign/consumed ticket')
  before,after,receipt=self._pending[token]
  if before is not self._state:
   del self._pending[token];raise ValueError('stale ticket')
  # Receipts have nested dictionaries: callers receive a fully independent copy.
  from copy import deepcopy
  result=deepcopy(receipt);self._state=after;del self._pending[token];return result
