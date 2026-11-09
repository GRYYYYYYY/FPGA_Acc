"""Bounded recursive SAT search with independently replayable RUP additions."""
from collections import Counter
class Limit(Exception): pass

def solve(clauses,variables,max_nodes=10000):
 database=[tuple(dict.fromkeys(c)) for c in clauses]; learned=[];visited=0
 def propagate(decisions):
  assignment={abs(x):x>0 for x in decisions}
  while True:
   residual=[];unit=None
   for clause in database:
    if any(assignment.get(abs(x))==(x>0) for x in clause):continue
    remaining=tuple(x for x in clause if abs(x) not in assignment)
    if not remaining:return assignment,None
    residual.append(remaining)
    if len(remaining)==1:unit=remaining[0];break
   if unit is None:return assignment,residual
   assignment[abs(unit)]=unit>0
 def visit(decisions):
  nonlocal visited
  visited+=1
  if visited>max_nodes:raise Limit()
  assignment,residual=propagate(decisions)
  if residual is None:
   clause=[-x for x in decisions];database.append(tuple(clause));learned.append(clause);return None
  if not residual:return {v:assignment.get(v,False) for v in range(1,variables+1)}
  shortest=min(map(len,residual));counts=Counter(abs(x) for c in residual if len(c)==shortest for x in c);var=min(counts,key=lambda v:(-counts[v],v))
  for lit in (var,-var):
   model=visit(decisions+[lit])
   if model is not None:return model
  # The two child nogoods imply this parent nogood by unit propagation.
  clause=[-x for x in decisions];database.append(tuple(clause));learned.append(clause)
  return None
 try:
  model=visit([]);status='SAT' if model is not None else 'UNSAT'
 except Limit:model=None;status='UNKNOWN_SEARCH_LIMIT'
 return dict(status=status,visited_nodes=visited,model=model,rup_additions=learned)
