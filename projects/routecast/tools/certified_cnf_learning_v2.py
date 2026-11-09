"""Bounded recursive SAT search with independently replayable RUP additions."""
from collections import Counter, defaultdict, deque
class Limit(Exception): pass

def solve(clauses,variables,max_nodes=10000):
 database=[tuple(dict.fromkeys(c)) for c in clauses]; learned=[];visited=0
 def propagate(decisions):
  assignment={};remaining={i:c for i,c in enumerate(database)};occ=defaultdict(set)
  for i,c in remaining.items():
   for x in c:occ[x].add(i)
  queue=deque(decisions);queue.extend(c[0] for c in remaining.values() if len(c)==1)
  if any(not c for c in remaining.values()):return assignment,None
  while queue:
   lit=queue.popleft();var=abs(lit)
   if var in assignment:
    if assignment[var]!=(lit>0):return assignment,None
    continue
   assignment[var]=lit>0
   for i in occ[lit]:remaining.pop(i,None)
   for i in occ[-lit]:
    if i not in remaining:continue
    remaining[i]=tuple(x for x in remaining[i] if x!=-lit)
    if not remaining[i]:return assignment,None
    if len(remaining[i])==1:queue.append(remaining[i][0])
  return assignment,list(remaining.values())
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
