"""Exact finite-domain feasibility for unit per-option resource consumption."""
from collections import Counter

def solve(options,capacities):
 """Options: row -> option ID -> iterable of distinct consumed resources.

 Deterministic search, no state mutation, no objective minimization. Exhaustive
 failure applies only to the supplied finite domains.
 """
 domains={r:{o:frozenset(resources) for o,resources in opts.items()} for r,opts in options.items()}
 if any(type(c) is not int or c<0 for c in capacities.values()):raise ValueError('capacity')
 if any(p not in capacities for opts in domains.values() for rs in opts.values() for p in rs):raise ValueError('resource domain')
 usage=Counter();chosen={};states=0
 def visit():
  nonlocal states
  states+=1
  if len(chosen)==len(domains):return True
  available={r:[o for o,rs in opts.items() if all(usage[p]<capacities[p] for p in rs)] for r,opts in domains.items() if r not in chosen}
  r=min(available,key=lambda r:(len(available[r]),r))
  for o in sorted(available[r]):
   chosen[r]=o;usage.update(domains[r][o])
   if visit():return True
   usage.subtract(domains[r][o]);del chosen[r]
  return False
 feasible=visit()
 return dict(feasible=feasible,assignment=dict(chosen) if feasible else {},search_states=states)
