"""Input-A support preference with unchanged raw-budget feasibility fallback.

Preference minimizes destination CHANNEL visits outside the input A support,
then raw path delay. It is not global aggregate L1 projection or an exact
budget-constrained optimum. Weighted paths are primal candidates only.
Only a separate raw minimum/cut certificate may justify budget pruning.
"""
from wide_cost_search_bridge_v2 import Forward
from masked_raw_forward_v1 import Search

class Oracle:
 def __init__(self,fields,rc,binary,channel_ids,A_support):
  self.raw=Search(fields,rc,binary)
  try:self.preferred=Forward(fields,rc,binary)
  except BaseException:self.raw.close();raise
  self.caps=tuple(fields['capacities']);self.n=len(self.caps);self.rc=rc
  try:
   channels=frozenset(channel_ids);support=frozenset(A_support)
   if not support<=channels or any(type(n) is not int or not 0<=n<self.n or not self.caps[n] for n in channels):raise ValueError('A/channel support domain')
   self.outside=channels-support;self.weight=(self.n-1)*max(rc.increments,default=0)+max(self.preferred.initial,default=0)+1
   self.preferred.prepare({n:1 for n in self.outside},self.weight)
  except BaseException:self.close();raise
 def close(self):
  self.raw.close();self.preferred.close()
 def _weighted(self,source,targets,blocked):
  e=self.preferred
  for n in {source}|targets|blocked:
   if type(n) is not int or not 0<=n<self.n:raise ValueError('node domain')
  if source in blocked or targets&blocked or any(not self.caps[n] for n in {source}|targets):raise ValueError('disabled endpoint')
  try:
   for n in blocked:e.cap[n]=0
   raw,parents,reached=e.search(source,targets);answers={}
   for sink in sorted(targets):
    if sink not in reached:answers[sink]={'reachable':False};continue
    node=sink;seen={node};slots=[]
    while node!=source:
     parent,slot=parents[node]
     if parent in seen:raise ValueError('cyclic parent')
     seen.add(parent);slots.append(int(slot));node=parent
    slots.reverse();value=e.initial[source]+sum(self.rc.increments[x] for x in slots);assert value==raw[sink]
    count=sum(e.dest[x] in self.outside for x in slots);answers[sink]={'reachable':True,'raw_cost':value,'slots':slots,'outside_A_visits':count,'weighted_objective':value+self.weight*count}
   return answers
  finally:
   for n in blocked:e.cap[n]=self.caps[n]
 def query(self,source,budgets_by_sink,blocked):
  budgets=dict(budgets_by_sink);targets=set(budgets);blocked=frozenset(blocked)
  if not budgets or any(type(b) is not int or b<0 for b in budgets.values()):raise ValueError('integer original budgets required')
  preferred=self._weighted(source,targets,blocked)
  if all(a['reachable'] and a['raw_cost']<=budgets[n] for n,a in preferred.items()):
   return {'kind':'A_SUPPORT_PRIMAL','within_budget':True,'answers':preferred,'raw_certificate':None,'pruning_allowed':False,'weighted_searches':1,'raw_searches':0}
  certificate=self.raw.query(source,targets,blocked);answers={}
  for n,a in certificate['answers'].items():
   answers[n]=dict(a)
   if a['reachable']:answers[n]['raw_cost']=a['minimum']
  passed=all(a['reachable'] and a['raw_cost']<=budgets[n] for n,a in answers.items())
  return {'kind':'RAW_FEASIBLE_FALLBACK' if passed else 'RAW_INFEASIBLE_CERTIFICATE','within_budget':passed,'answers':answers,'raw_certificate':certificate,'pruning_allowed':not passed,'weighted_searches':1,'raw_searches':1}
