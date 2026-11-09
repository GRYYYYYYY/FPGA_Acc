"""Prevalidated supplied-path enumeration with exact integer costs and undo.

No objective pruning: a higher-criticality new user can reduce an existing
node's congestion charge. State limit counts visit frames, not reference full
combinations. Only exhausted search promises supplied-candidate optimum.
"""
import math
from fractions import Fraction
from budget_NET_gate_reference_v1 import audit
from criticality_whole_net_choice_reference_v1 import score

def choose(adjacency,source,budgets,old_paths,candidates,pins,congestion,initial_raw=0,capacities=None,max_states=10000):
 if type(max_states) is not int or max_states<1 or set(candidates)!=set(budgets) or set(s for s,_ in pins)!=set(budgets):raise ValueError('scope/state cap')
 pins=tuple(pins)
 if any(not isinstance(c,Fraction) or not 0<=c<=1 for _,c in pins):raise ValueError('criticality')
 denominator=math.lcm(*(c.denominator for _,c in pins));sumc={s:0 for s in budgets};maxc={s:0 for s in budgets}
 for s,c in pins:
  value=c.numerator*(denominator//c.denominator);sumc[s]+=value;maxc[s]=max(maxc[s],value)
 oldaudit=audit(adjacency,source,budgets,old_paths,initial_raw,capacities);oldscore=score(adjacency,source,old_paths,pins,congestion,initial_raw);best=int(oldscore*denominator);bestpaths={s:list(p) for s,p in old_paths.items()}
 sinks=sorted(budgets);valid={};prices={}
 for s in sinks:
  seen=set();valid[s]=[]
  for path in [old_paths[s],*candidates[s]]:
   path=tuple(path)
   if path in seen:continue
   seen.add(path)
   try:check=audit(adjacency,source,{s:budgets[s]},{s:path},initial_raw,capacities)
   except ValueError:continue
   for node in check['parents']:
    value=congestion.get(node,0)
    if type(value) is not int or value<0:raise ValueError('congestion')
    prices[node]=value
   valid[s].append((path,check['parents'],(check['delays'][s]-initial_raw)*sumc[s]))
 parents={};users={};paths={};states=0;limited=False
 stack=[('visit',0,None,initial_raw*sum(sumc.values()))]
 while stack:
  frame=stack.pop()
  if frame[0]=='undo':
   _,sink,added,changed=frame
   del paths[sink]
   for node in added:del parents[node]
   for node,previous in changed:
    if previous is None:del users[node]
    else:users[node]=previous
   continue
  if states==max_states:limited=True;break
  _,index,option,cost=frame;states+=1
  if option is not None:
   sink=sinks[index-1];path,newparents,rawcost=option
   if any(node in parents and parents[node]!=parent for node,parent in newparents.items()):continue
   added=[];changed=[];cost+=rawcost
   for node,parent in newparents.items():
    if node not in parents:parents[node]=parent;added.append(node)
    previous=users.get(node);nextvalue=max(previous if previous is not None else 0,maxc[sink])
    if previous is None:cost+=(denominator-nextvalue)*prices[node]
    else:cost+=(previous-nextvalue)*prices[node]
    users[node]=nextvalue;changed.append((node,previous))
   paths[sink]=path;stack.append(('undo',sink,added,changed))
  if index==len(sinks):
   if cost<best:best=cost;bestpaths={s:list(p) for s,p in paths.items()}
   continue
  for option in reversed(valid[sinks[index]]):stack.append(('visit',index+1,option,cost))
 chosen=audit(adjacency,source,budgets,bestpaths,initial_raw,capacities);verified=score(adjacency,source,bestpaths,pins,congestion,initial_raw)
 if verified!=Fraction(best,denominator):raise RuntimeError('undo score mismatch')
 return dict(status='ACCEPT_STRICT_IMPROVEMENT' if verified<oldscore else 'RETAIN',paths=bestpaths,audit=chosen,old_score=oldscore,chosen_score=verified,states=states,search_status='UNKNOWN_STATE_LIMIT' if limited else 'OPTIMAL_WITHIN_SUPPLIED_CANDIDATES')
