"""Bounded supplied-path NET selection under a frozen per-pin objective.

Sum criticality-weighted per-pin raw delays plus unique-node congestion charged
at (1 - maximum criticality of users). With descending criticality processing,
this is the first user charge for each new node. This comparison objective is
not native routing equivalence or the old unweighted union objective.
"""
from fractions import Fraction
from itertools import product
from budget_NET_gate_reference_v1 import audit

def score(adjacency,source,paths,pins,congestion,initial_raw=0):
 users={};delay_total=Fraction(0)
 for sink,criticality in pins:
  if not isinstance(criticality,Fraction) or not 0<=criticality<=1:raise ValueError('criticality')
  u=source;raw=initial_raw
  for edge in paths[sink]:
   matches=[a for a in adjacency.get(u,()) if a[0]==edge]
   if len(matches)!=1:raise ValueError('arc')
   _,v,r,_=matches[0];raw+=r;users[v]=max(users.get(v,Fraction(0)),criticality);u=v
  if u!=sink:raise ValueError('endpoint')
  delay_total+=criticality*raw
 price=Fraction(0)
 for node,maximum in users.items():
  value=congestion.get(node,0)
  if type(value) is not int or value<0:raise ValueError('congestion')
  price+=(1-maximum)*value
 return delay_total+price

def choose(adjacency,source,budgets,old_paths,candidates,pins,congestion,initial_raw=0,capacities=None,max_states=10000):
 if type(max_states) is not int or max_states<1 or set(candidates)!=set(budgets):raise ValueError('candidate scope/state cap')
 if set(s for s,_ in pins)!=set(budgets):raise ValueError('pin coverage')
 old=audit(adjacency,source,budgets,old_paths,initial_raw,capacities)
 old_score=score(adjacency,source,old_paths,pins,congestion,initial_raw)
 chosen={s:list(p) for s,p in old_paths.items()};best=old_score;chosen_audit=old
 sinks=sorted(budgets);valid={}
 for s in sinks:
  valid[s]=[];seen=set()
  for path in [old_paths[s],*candidates[s]]:
   path=tuple(path)
   if path in seen:continue
   seen.add(path)
   try:audit(adjacency,source,{s:budgets[s]},{s:path},initial_raw,capacities)
   except ValueError:continue
   valid[s].append(path)
 states=0;limited=False
 for paths in product(*(valid[s] for s in sinks)):
  if states==max_states:limited=True;break
  states+=1;proposal=dict(zip(sinks,paths))
  try:check=audit(adjacency,source,budgets,proposal,initial_raw,capacities)
  except ValueError:continue
  value=score(adjacency,source,proposal,pins,congestion,initial_raw)
  if value<best:chosen={s:list(p) for s,p in proposal.items()};best=value;chosen_audit=check
 return dict(status='ACCEPT_STRICT_IMPROVEMENT' if best<old_score else 'RETAIN',paths=chosen,audit=chosen_audit,old_score=old_score,chosen_score=best,states=states,search_status='UNKNOWN_STATE_LIMIT' if limited else 'OPTIMAL_WITHIN_SUPPLIED_CANDIDATES')
