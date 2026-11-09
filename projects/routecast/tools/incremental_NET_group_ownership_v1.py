"""Serial COW ownership for already admitted channel-path node projections.

This validates membership/accounting, not physical paths, RC, or route admission.
Each CID owns a set of eligible nodes; sibling references share one NET owner.
"""
from collections import Counter,defaultdict,namedtuple
from incremental_IPIN_feature_cache_v1 import pages,lookup,patched
from net_group_collision_risk_v1 import unit_group_expectation
State=namedtuple('State','generation queries nets hist features')

class Cache:
 def __init__(self,graph_epoch,groups,records):
  if not isinstance(graph_epoch,str) or not graph_epoch:raise ValueError('graph epoch')
  self._epoch=graph_epoch;self._sizes={};self._group_of={}
  for gid,nodes in groups.items():
   if type(gid) is not int or gid<0 or not nodes:raise ValueError('group')
   self._sizes[gid]=len(nodes)
   for node in nodes:
    if type(node) is not int or node<0 or node in self._group_of:raise ValueError('node domain')
    self._group_of[node]=gid
  queries={};refs=defaultdict(Counter)
  for row in records:
   cid,value=self._normalize(row)
   if cid in queries:raise ValueError('duplicate CID')
   queries[cid]=value;refs[value[0]].update(value[1])
  nets={};hist=defaultdict(Counter)
  for net,counts in refs.items():
   ks=Counter(self._group_of[n] for n in counts);nets[net]=(counts,ks)
   for gid,k in ks.items():hist[gid][k]+=1
  features={gid:self._feature(gid,h) for gid,h in hist.items()}
  self._state=State(0,pages(queries),pages(nets),pages(dict(hist)),pages(features));self._pending={}
 def _normalize(self,row):
  if set(row)!={'connection_id','net_id','nodes'}:raise ValueError('record schema')
  cid,net=row['connection_id'],row['net_id']
  if type(cid) is not int or cid<0 or type(net) is not int or net<0:raise ValueError('identity')
  nodes=row['nodes']
  if not isinstance(nodes,(list,tuple,set,frozenset)) or any(type(n) is not int or n not in self._group_of for n in nodes):raise ValueError('projected nodes')
  return cid,(net,frozenset(nodes))
 def _feature(self,gid,h):
  v=unit_group_expectation(self._sizes[gid],h)
  return (v['expected_occupancy'],v['probability_empty'],v['expected_overflow'])
 @property
 def generation(self):return self._state.generation
 def snapshot(self):
  s=self._state
  return dict(generation=s.generation,queries={cid:(v[0],tuple(sorted(v[1]))) for p in s.queries for cid,v in p.items()},nets={net:(dict(v[0]),dict(v[1])) for p in s.nets for net,v in p.items()},histograms={g:dict(h) for p in s.hist for g,h in p.items()},features={g:lookup(s.features,g,self._feature(g,{})) for g in self._sizes})
 def prepare(self,graph_epoch,generation,edits):
  before=self._state
  if graph_epoch!=self._epoch or type(generation) is not int or generation!=before.generation:raise ValueError('graph/generation mismatch')
  if not edits:raise ValueError('empty batch')
  changes={};node_deltas=defaultdict(Counter)
  for edit in edits:
   if set(edit)!={'old','new'}:raise ValueError('edit schema')
   cid,old=self._normalize(edit['old']);newcid,new=self._normalize(edit['new'])
   if cid in changes or newcid!=cid or old[0]!=new[0]:raise ValueError('fixed CID/NET')
   if lookup(before.queries,cid)!=old or old==new:raise ValueError('stale/noop path projection')
   changes[cid]=new
   for n in old[1]-new[1]:node_deltas[old[0]][n]-=1
   for n in new[1]-old[1]:node_deltas[old[0]][n]+=1
  nets={};hist={};reference_events=0;ownership_events=0
  for net,deltas in node_deltas.items():
   oldrefs,oldks=lookup(before.nets,net);refs=Counter(oldrefs);ks=Counter(oldks);touched=set()
   for n,delta in deltas.items():
    if not delta:continue
    previous=refs[n];following=previous+delta
    if following<0:raise ValueError('reference underflow')
    if following:refs[n]=following
    else:refs.pop(n,None)
    reference_events+=1
    difference=int(following>0)-int(previous>0)
    if difference:
     gid=self._group_of[n];ks[gid]+=difference;touched.add(gid);ownership_events+=1
   for gid in touched:
    oldk,newk=oldks.get(gid,0),ks.get(gid,0)
    if not newk:ks.pop(gid,None)
    if oldk==newk:continue
    if gid not in hist:hist[gid]=Counter(lookup(before.hist,gid,{}))
    if oldk:
     hist[gid][oldk]-=1
     if not hist[gid][oldk]:del hist[gid][oldk]
    if newk:hist[gid][newk]+=1
   nets[net]=(refs,ks)
  features={g:self._feature(g,h) for g,h in hist.items()}
  q,qp,qe=patched(before.queries,changes);n,np,ne=patched(before.nets,nets)
  h,hp,he=patched(before.hist,{g:v if v else None for g,v in hist.items()})
  f,fp,fe=patched(before.features,{g:features[g] if hist[g] else None for g in hist})
  after=State(before.generation+1,q,n,h,f)
  receipt=dict(generation=after.generation,query_updates=len(changes),NET_updates=len(nets),reference_events=reference_events,ownership_events=ownership_events,touched_histogram_groups=tuple(sorted(hist)),copied_shards=qp+np+hp+fp,copied_shard_entries=qe+ne+he+fe)
  token=object();self._pending[token]=(before,after,receipt);return token
 def commit(self,token):
  if token not in self._pending:raise ValueError('foreign/consumed ticket')
  before,after,receipt=self._pending[token]
  if before is not self._state:
   del self._pending[token];raise ValueError('stale ticket')
  result=dict(receipt);self._state=after;del self._pending[token];return result
