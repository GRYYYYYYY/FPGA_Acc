"""Dominators in an admitted acyclic parent-choice support; no global graph claim."""
def mandatory(prepared):
 source=prepared['source'];labels=prepared['distance'];choices=prepared['choices'];assert source in labels and set(choices)==set(labels)-{source};dominators={source:frozenset([source])}
 for n in sorted(labels,key=lambda v:(labels[v][1],v)):
  if n==source:continue
  parents=choices[n];assert parents
  for u,_ in parents:assert labels[u][1]+1==labels[n][1] and u in dominators
  common=set(dominators[parents[0][0]])
  for u,_ in parents[1:]:common.intersection_update(dominators[u])
  common.add(n);dominators[n]=frozenset(common)
 witnesses={}
 for sink in sorted(prepared['sinks']):
  for n in dominators[sink]:witnesses.setdefault(n,sink)
 return witnesses
