"""Necessary unit-resource ownership relaxation for certified per-NET budget cuts."""
from collections import defaultdict
from itertools import combinations

def encode(cuts):
 normalized=[]
 for cut in cuts:
  net=cut['NET'];nodes=tuple(sorted(set(cut['nodes'])))
  if type(net) is not int or net<0 or not nodes or any(type(n) is not int or n<0 for n in nodes):raise ValueError('cut domain')
  normalized.append((net,nodes))
 pairs=sorted({(node,net) for net,nodes in normalized for node in nodes});index={pair:i+1 for i,pair in enumerate(pairs)};clauses=set();owners=defaultdict(list)
 for net,nodes in normalized:clauses.add(tuple(sorted(index[node,net] for node in nodes)))
 for node,net in pairs:owners[node].append(index[node,net])
 for node,variables in owners.items():
  for a,b in combinations(variables,2):clauses.add(tuple(sorted((-a,-b))))
 return dict(variables=[dict(kind='OWNER',node=node,NET=net) for node,net in pairs],clauses=[list(c) for c in sorted(clauses)],scope='Each NET must own at least one unit node from each of its certified cuts. Same NET may satisfy multiple cuts with one node; a node may have at most one NET owner. Necessary budget-path conditions, no flow/tree sufficiency.')
