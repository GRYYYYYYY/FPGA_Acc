"""Serial graph/generation-bound IPIN feature cache with sharded COW commits.

Fixed CID/NET domain, source-driver consistency, duplicate NET/class references.
Feature state only: this is not placement/path admission or native state.
"""
from collections import Counter,defaultdict,namedtuple
from fractions import Fraction

SHARDS=1024
Snapshot=namedtuple('Snapshot','generation queries owners features nets')
ZERO=(0,Fraction(0),Fraction(0))

def pages(mapping):
 result=[{} for _ in range(SHARDS)]
 for key,value in mapping.items():result[key%SHARDS][key]=value
 return tuple(result)

def lookup(parts,key,default=None):return parts[key%SHARDS].get(key,default)

def patched(parts,updates):
 result=list(parts);copied=set();entries=0
 for key,value in updates.items():
  i=key%SHARDS
  if i not in copied:result[i]=dict(parts[i]);copied.add(i);entries+=len(parts[i])
  if value is None:result[i].pop(key,None)
  else:result[i][key]=value
 return tuple(result),len(copied),entries

def feature(size,q):
 return (q,Fraction(q,size),Fraction(q,size)-1+Fraction(size-1,size)**q) if q else ZERO

class Cache:
 def __init__(self,graph_epoch,sink_sizes,valid_sources,connections):
  if not isinstance(graph_epoch,str) or not graph_epoch:raise ValueError('graph epoch')
  if any(type(s) is not int or s<0 or type(m) is not int or m<1 for s,m in sink_sizes.items()):raise ValueError('sink groups')
  self._graph=graph_epoch;self._sizes=dict(sink_sizes);self._sources=frozenset(valid_sources)
  if any(type(s) is not int or s<0 for s in self._sources):raise ValueError('source domain')
  queries={};owners=defaultdict(Counter);nets={}
  for row in connections:
   cid,value=self._normalize(row);net,source,sink=value
   if cid in queries:raise ValueError('duplicate CID')
   if net in nets and nets[net][0]!=source:raise ValueError('inconsistent NET source')
   queries[cid]=value;owners[sink][net]+=1;nets[net]=(source,nets.get(net,(source,0))[1]+1)
  features={sink:feature(self._sizes[sink],len(counts)) for sink,counts in owners.items()}
  self._state=Snapshot(0,pages(queries),pages(dict(owners)),pages(features),pages(nets));self._pending={}
 def _normalize(self,row):
  if set(row)!= {'connection_id','net_id','source','sink'} or any(type(v) is not int or v<0 for v in row.values()):raise ValueError('query schema')
  if row['sink'] not in self._sizes or row['source'] not in self._sources:raise ValueError('graph endpoint domain')
  return row['connection_id'],(row['net_id'],row['source'],row['sink'])
 @property
 def generation(self):return self._state.generation
 @property
 def graph_epoch(self):return self._graph
 def class_feature(self,sink):
  if sink not in self._sizes:raise ValueError('unknown class')
  return lookup(self._state.features,sink,ZERO)
 def query(self,cid):
  value=lookup(self._state.queries,cid)
  if value is None:raise ValueError('unknown CID')
  return dict(connection_id=cid,net_id=value[0],source=value[1],sink=value[2])
 def snapshot(self):
  state=self._state
  queries={cid:value for part in state.queries for cid,value in part.items()}
  return dict(graph_epoch=self._graph,generation=state.generation,connections=[dict(connection_id=cid,net_id=v[0],source=v[1],sink=v[2]) for cid,v in sorted(queries.items())],owner_multiplicities={s:dict(v) for part in state.owners for s,v in part.items()},features={s:self.class_feature(s) for s in sorted(self._sizes)})
 def prepare(self,expected_graph_epoch,expected_generation,edits):
  before=self._state
  if expected_graph_epoch!=self._graph:raise ValueError('graph epoch mismatch')
  if type(expected_generation) is not int or expected_generation!=before.generation:raise ValueError('stale generation')
  if not edits:raise ValueError('empty batch')
  changes={};touched=set();driver_counts={}
  for edit in edits:
   if set(edit)!= {'old','new'}:raise ValueError('edit schema')
   cid,old=self._normalize(edit['old']);newcid,new=self._normalize(edit['new'])
   if cid in changes or newcid!=cid or old[0]!=new[0]:raise ValueError('fixed CID/NET identity')
   if lookup(before.queries,cid)!=old:raise ValueError('stale endpoint descriptor')
   if old==new:raise ValueError('unchanged edit')
   changes[cid]=(old,new)
   if old[2]!=new[2]:touched.update([old[2],new[2]])
   net=old[0]
   if net not in driver_counts:
    source,count=lookup(before.nets,net);driver_counts[net]=Counter({source:count})
   driver_counts[net][old[1]]-=1;driver_counts[net][new[1]]+=1
  net_updates={}
  for net,counts in driver_counts.items():
   active={s:n for s,n in counts.items() if n}
   if len(active)!=1 or any(n<0 for n in active.values()):raise ValueError('partial/inconsistent NET driver update')
   source,count=next(iter(active.items()))
   if lookup(before.nets,net)!=(source,count):net_updates[net]=(source,count)
  owners={s:Counter(lookup(before.owners,s,{})) for s in touched}
  for old,new in changes.values():
   if old[2]==new[2]:continue
   count=owners[old[2]][old[0]]
   if count<1:raise ValueError('owner count underflow')
   owners[old[2]][old[0]]-=1
   if not owners[old[2]][old[0]]:del owners[old[2]][old[0]]
   owners[new[2]][new[0]]+=1
  features={s:feature(self._sizes[s],len(counts)) for s,counts in owners.items()}
  changed_counts=tuple(sorted(s for s in touched if features[s][0]!=lookup(before.features,s,ZERO)[0]))
  new_queries,qpages,qentries=patched(before.queries,{cid:new for cid,(old,new) in changes.items()})
  new_owners,opages,oentries=patched(before.owners,{s:counts if counts else None for s,counts in owners.items()})
  new_features,fpages,fentries=patched(before.features,{s:values if values[0] else None for s,values in features.items()})
  new_nets,npages,nentries=patched(before.nets,net_updates)
  after=Snapshot(before.generation+1,new_queries,new_owners,new_features,new_nets)
  receipt=dict(generation=after.generation,endpoint_updates=len(changes),sink_membership_updates=sum(old[2]!=new[2] for old,new in changes.values()),touched_classes=tuple(sorted(touched)),changed_count_classes=changed_counts,copied_shards=qpages+opages+fpages+npages,copied_shard_entries=qentries+oentries+fentries+nentries,shards_per_map=SHARDS)
  token=object();self._pending[token]=(before,after,receipt);return token
 def commit(self,token):
  if token not in self._pending:raise ValueError('foreign or consumed ticket')
  before,after,receipt=self._pending[token]
  if self._state is not before:
   del self._pending[token];raise ValueError('stale prepared ticket')
  result=dict(receipt)
  self._state=after;del self._pending[token]
  return result
