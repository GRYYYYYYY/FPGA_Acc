"""Input-defined coupling graph for separable aggregate resource-count objectives."""
from collections import defaultdict
from itertools import combinations

def interactions(pools):
 variable={};users=defaultdict(list)
 for net,choices in sorted(pools.items()):
  if not choices:raise ValueError('empty NET candidate pool')
  possible=set.union(*(set(c) for c in choices));mandatory=set.intersection(*(set(c) for c in choices));variable[net]=possible-mandatory
  for n in variable[net]:users[n].append(net)
 shared=defaultdict(set)
 for node,nets in users.items():
  for a,b in combinations(sorted(nets),2):shared[a,b].add(node)
 adjacency={net:set() for net in pools}
 for a,b in shared:adjacency[a].add(b);adjacency[b].add(a)
 components=[];unseen=set(pools)
 while unseen:
  start=min(unseen);unseen.remove(start);todo=[start];group=[]
  while todo:
   n=todo.pop();group.append(n)
   for v in sorted(adjacency[n]):
    if v in unseen:unseen.remove(v);todo.append(v)
  components.append(sorted(group))
 return {'variable':variable,'pairs':[(a,b,sorted(nodes)) for (a,b),nodes in sorted(shared.items())],'components':components}
