"""Pure1/2NET group plan on prevalidated physical tree descriptors; no commit."""
from collections import Counter
from fractions import Fraction

def evaluate(capacities,ledger,old,new,base,history,span,weight):
 if not 1<=len(old)<=2 or set(old)!=set(new):raise ValueError('group NET domain')
 n=len(capacities)
 if len(base)!=n or type(weight) is not int or weight<0:raise ValueError('price domain')
 def checked(tree):
  owned=tree['owned'];users=tree['users'];raw=tree['weighted_raw']
  if not owned or not set(users)<=set(owned) or raw<0:raise ValueError('tree descriptor')
  for node in owned:
   if type(node) is not int or not 0<=node<n or type(capacities[node]) is not int or capacities[node]<=0:raise ValueError('node domain')
  if any(not 0<=c<=1 for c in users.values()):raise ValueError('criticality')
  return owned
 removed=Counter(node for tree in old.values() for node in checked(tree));added=Counter(node for tree in new.values() for node in checked(tree));touched=set(removed)|set(added);costs={};updates={};pressure=0
 for node in touched:
  count=ledger.get(node,0)
  if type(count) is not int or count<removed[node]:raise ValueError('old owner absent')
  b=base[node];h=history.get(node,0);s=span.get(node,0)
  if any(type(x) is not int or x<0 for x in [b,h,s]):raise ValueError('negative price')
  other=count-removed[node];costs[node]=b*(1+h)*(1+max(0,other-capacities[node]+1))+weight*s;after=other+added[node];pressure+=max(0,after-capacities[node])-max(0,count-capacities[node])
  if after!=count:updates[node]=after
 def score(trees):return sum((Fraction(t['weighted_raw'])+sum((1-c)*costs[node] for node,c in t['users'].items()) for t in trees.values()),Fraction(0))
 a,b=score(old),score(new);accepted=pressure<=0 and b<=a
 return {'accepted':accepted,'status':'ADMIT_GROUP' if accepted else 'RETAIN_OBJECTIVE_INCREASE' if b>a else 'RETAIN_OVERFLOW_INCREASE','old_score':a,'candidate_score':b,'objective_delta':b-a,'overflow_delta':pressure,'updates':updates if accepted else {},'rejected_updates':{} if accepted else updates}
