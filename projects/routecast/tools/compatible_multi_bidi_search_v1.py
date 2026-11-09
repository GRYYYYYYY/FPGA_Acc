"""New path policy: independently optimal small-target paths, merge or forward fallback."""
from collections import Counter
from types import SimpleNamespace
from hybrid_bidirectional_search_v1 import Search as Base
class Search(Base):
 def __init__(self,fields,rc,binary,*,target_limit=4):
  if not isinstance(target_limit,int) or target_limit<2:raise ValueError('target_limit must be integer >=2')
  f={k:tuple(v) for k,v in fields.items()};initial=tuple(rc.initial(u) for u in range(len(f['capacities'])));snapshot=SimpleNamespace(increments=tuple(rc.increments),initial=initial.__getitem__)
  super().__init__(f,snapshot,binary);self.target_limit=target_limit;self.stats=Counter();self.closed=False
 def prepare(self,prices,weight):
  if self.closed:raise RuntimeError('closed search')
  n=self.forward.n;values=tuple(prices.get(u,0) for u in range(n))
  if not isinstance(weight,int) or not 0<=weight<2**64 or any(not isinstance(v,int) or not 0<=v<2**64 for v in values):raise ValueError('invalid price/weight')
  if 2*n*(self.forward.maxinc+weight*max(values,default=0))+max(self.rc.initial(u) for u in range(n))>=2**120:raise ValueError('cost envelope exceeded')
  super().prepare(dict(enumerate(values)),weight);self.prices=values;self.weight=weight
 def search(self,source,sinks):
  if self.closed:raise RuntimeError('closed search')
  targets=set(sinks);self.stats['requests']+=1
  if not 2<=len(targets)<=self.target_limit:self.stats['original_policy']+=1;return super().search(source,targets)
  n=self.forward.n
  if not 0<=source<n or any(not 0<=t<n for t in targets):return self.forward.search(source,targets)
  if not self.fields['capacities'][source] or any(not self.fields['capacities'][t] for t in targets):self.stats['capacity_fallback']+=1;return self.forward.search(source,targets)
  parents={};answers={};reason=None;self.stats['multi_attempts']+=1
  for t in sorted(targets):
   a=self.bidirectional.search(source,t);self.stats['bidi_calls']+=1
   if a is None:reason='unreachable';break
   self.stats['bidi_scans']+=sum(a['scanned_arcs']);u=source;seen={u}
   for e in a['slots']:
    if not self.fields['row_offsets'][u]<=e<self.fields['row_offsets'][u+1]:raise RuntimeError('invalid bidi arc')
    v=self.fields['dest_ranks'][e]
    if v in seen:raise RuntimeError('invalid bidi path cycle')
    incoming=(u,e)
    if v in parents and parents[v]!=incoming:reason='parent_conflict';break
    parents[v]=incoming;seen.add(v);u=v
   if reason:break
   if u!=t:raise RuntimeError('wrong bidi terminal')
   answers[t]=a
  if reason:
   self.stats[reason+'_fallback']+=1;return self.forward.search(source,targets)
  raw={source:self.rc.initial(source)}
  for t in sorted(targets):
   u=t;path=[];seen={u}
   while u!=source:
    if u not in parents:raise RuntimeError('incomplete merged parents')
    prev,e=parents[u];path.append(e);u=prev
    if u in seen:raise RuntimeError('merged cycle')
    seen.add(u)
   original=self.rc.initial(source)+sum(self.rc.increments[e] for e in path);objective=original+sum(self.weight*self.prices[self.fields['dest_ranks'][e]] for e in path)
   if original!=answers[t]['raw'] or objective!=answers[t]['objective']:raise RuntimeError('merged cost changed')
   raw[t]=original
  self.stats['merged']+=1;return raw,parents,targets
 def close(self):
  super().close();self.closed=True
