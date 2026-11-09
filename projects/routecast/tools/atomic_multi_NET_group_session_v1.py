"""Serial atomic snapshot publisher for the separate multi-NET group prototype.

Fixed graph, copied RC/identities, detached immutable records/ledger/epochs.
Global generation invalidates all competing tickets, conservatively including
unrelated NET changes. Prices are caller-supplied frozen group snapshots; this
module does not establish their native equivalence or compute a joint search.
"""
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
from threading import RLock
from types import MappingProxyType
from criticality_multi_NET_group_admission_v2 import prepare as admit
from criticality_net_admission_v1 import validate

def freeze(value):
 if type(value) in (dict,MappingProxyType):return MappingProxyType({freeze(k):freeze(v) for k,v in value.items()})
 if type(value) in (list,tuple):return tuple(freeze(v) for v in value)
 if type(value) in (int,str,bool,float,type(None),Fraction):return value
 raise ValueError('unsupported mutable or opaque snapshot value')

@dataclass(frozen=True)
class Snapshot:
 generation:int
 price_epoch:int
 records:object
 ledger:object
 epochs:object

class FrozenRC:
 def __init__(self,rc,n,m):
  self._initial=tuple(rc.initial(i) for i in range(n));self._increments=tuple(rc.increment(i) for i in range(m))
  if any(type(v) is not int or v<0 for v in self._initial+self._increments):raise ValueError('RC snapshot domain')
 def initial(self,node):return self._initial[node]
 def increment(self,slot):return self._increments[slot]

class Session:
 def __init__(self,fields,rc,slots,queries,records,ledger,criticalities,epochs):
  self._lock=RLock();self._closed=False;self._pending={}
  self._fields=MappingProxyType({k:tuple(fields[k]) for k in ['capacities','row_offsets','dest_ranks','edge_ids']});self._slots=MappingProxyType(dict(slots));self._rc=FrozenRC(rc,len(fields['capacities']),len(fields['edge_ids']));self._queries=freeze(queries);self._criticalities=freeze(criticalities)
  nets=set(queries)
  if not nets or set(records)!=nets or set(epochs)!=nets or any(type(n) is not int or n<0 for n in nets):raise ValueError('initial NET domain')
  if any(type(v) is not int or v<0 for v in epochs.values()):raise ValueError('initial epoch domain')
  frozen=freeze(records);rebuilt=Counter();ids=set()
  for net in nets:
   if any(q['net_id']!=net for q in self._queries[net]):raise ValueError('NET query identity')
   qids={q['connection_id'] for q in self._queries[net]}
   if ids&qids:raise ValueError('duplicate global CID')
   ids.update(qids);a=validate(self._fields,self._rc,self._slots,self._queries[net],frozen[net]);rebuilt.update(a['owned'])
  if any(type(n) is not int or type(v) is not int or v<=0 for n,v in ledger.items()) or dict(rebuilt)!=dict(ledger):raise ValueError('initial ledger mismatch')
  self._state=Snapshot(0,0,frozen,freeze(dict(ledger)),freeze(dict(epochs)))
 def _check(self,generation):
  if self._closed:raise RuntimeError('closed group session')
  if type(generation) is not int or generation!=self._state.generation:raise RuntimeError('stale group generation')
 def snapshot(self):
  with self._lock:
   if self._closed:raise RuntimeError('closed group session')
   return self._state
 def prepare(self,candidates,node_costs,*,generation,expected_epochs,price_epoch):
  with self._lock:
   self._check(generation);state=self._state
   if type(price_epoch) is not int or price_epoch!=state.price_epoch:raise RuntimeError('stale group price epoch')
   if not candidates or not set(candidates)<=set(state.records):raise ValueError('candidate NET scope')
   frozen=freeze(candidates);prices=dict(node_costs)
   if any(type(n) is not int or not 0<=n<len(self._fields['capacities']) or type(v) is not int or v<0 for n,v in prices.items()):raise ValueError('price domain')
   nets=set(frozen);queries={n:self._queries[n] for n in nets};old={n:state.records[n] for n in nets};plan=admit(self._fields,self._rc,self._slots,queries,old,frozen,state.ledger,self._criticalities,MappingProxyType(prices),state.epochs,dict(expected_epochs));summary={k:plan[k] for k in ['accepted','status','prospective_overflow_delta','old_score','candidate_score','objective_delta']}
   if not plan['accepted']:return None,summary
   records=dict(state.records);records.update(frozen);ledger=dict(state.ledger)
   for n,v in plan['updates'].items():
    if v:ledger[n]=v
    else:ledger.pop(n,None)
   epochs=dict(state.epochs)
   for n in nets:epochs[n]+=1
   candidate=Snapshot(state.generation+1,state.price_epoch,MappingProxyType(records),MappingProxyType(ledger),MappingProxyType(epochs));ticket=object();self._pending[ticket]=(state.generation,state.price_epoch,candidate)
   return ticket,summary
 def commit(self,ticket,*,generation,price_epoch):
  with self._lock:
   self._check(generation)
   if type(price_epoch) is not int or price_epoch!=self._state.price_epoch:raise RuntimeError('stale publication price epoch')
   if type(ticket) is not object or ticket not in self._pending:raise ValueError('unknown group ticket')
   saved_generation,saved_price,candidate=self._pending[ticket]
   if (saved_generation,saved_price)!=(self._state.generation,self._state.price_epoch):raise RuntimeError('stale group ticket')
   empty={}
   self._state=candidate # Single publication point; readers never see partial NET updates.
   self._pending=empty
   return candidate.generation
 def advance_price_epoch(self,*,generation):
  with self._lock:
   self._check(generation);s=self._state;candidate=Snapshot(s.generation+1,s.price_epoch+1,s.records,s.ledger,s.epochs);empty={};self._state=candidate;self._pending=empty;return candidate.generation
 def discard(self,ticket):
  with self._lock:
   if self._closed:raise RuntimeError('closed group session')
   if type(ticket) is not object or ticket not in self._pending:raise ValueError('unknown group ticket')
   del self._pending[ticket]
 def close(self):
  with self._lock:self._closed=True;self._pending.clear()
