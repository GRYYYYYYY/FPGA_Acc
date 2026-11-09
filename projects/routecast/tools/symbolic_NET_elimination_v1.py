"""Label-independent deterministic min-fill plan; not minimum-treewidth proof."""
from itertools import combinations
from math import prod

def plan(cardinalities,scopes):
 if not cardinalities or any(type(n) is not int or type(d) is not int or d<1 for n,d in cardinalities.items()):raise ValueError('variable domains')
 fixed=sorted(n for n,d in cardinalities.items() if d==1);active={n for n,d in cardinalities.items() if d>1};adj={n:set() for n in active};initial=[]
 for scope in scopes:
  if not set(scope)<=set(cardinalities):raise ValueError('unknown factor variable')
  scope=sorted(set(scope)&active);initial.append(scope)
  for a,b in combinations(scope,2):adj[a].add(b);adj[b].add(a)
 def score(n):
  neighbors=sorted(adj[n]);missing=sum(b not in adj[a] for a,b in combinations(neighbors,2));states=cardinalities[n]*prod(cardinalities[v] for v in neighbors)
  return missing,states,len(neighbors),n
 steps=[]
 while adj:
  v=min(adj,key=score);priority=score(v);neighbors=sorted(adj[v]);fill=[(a,b) for a,b in combinations(neighbors,2) if b not in adj[a]]
  for a,b in fill:adj[a].add(b);adj[b].add(a)
  for n in neighbors:adj[n].remove(v)
  del adj[v];cells=prod(cardinalities[n] for n in neighbors);steps.append({'NET':v,'neighbors':neighbors,'minfill_score':list(priority),'fill_edges':[list(e) for e in fill],'bag_states':cells*cardinalities[v],'separator_states':cells})
 return {'fixed_NETs':fixed,'steps':steps,'induced_width':max((len(s['neighbors']) for s in steps),default=0),'largest_bag_states':max((s['bag_states'] for s in steps),default=1),'largest_separator_states':max((s['separator_states'] for s in steps),default=1),'sum_bag_states':sum(s['bag_states'] for s in steps),'sum_separator_states':sum(s['separator_states'] for s in steps)}
