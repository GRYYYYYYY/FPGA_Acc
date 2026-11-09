"""Dependency-derived RUP with deterministic pure-literal decision batching."""
from collections import Counter,defaultdict,deque

def solve(clauses,variables,max_nodes=10000):
 database=[tuple(dict.fromkeys(c)) for c in clauses];learned=[];decisions=[];visited=0;backjumps=0;skipped=0;pure_batches=0;pure_literals=0;ordinary_literals=0
 occ=defaultdict(set)
 for i,c in enumerate(database):
  for lit in c:occ[lit].add(i)
 def propagate():
  assigned={};dependencies={};remaining={i:c for i,c in enumerate(database)}
  def causes(i,except_var=None):
   return set().union(*(dependencies[abs(x)] for x in database[i] if abs(x)!=except_var and abs(x) in assigned))
  queue=deque((lit,{lit}) for lit in decisions)
  queue.extend((c[0],set()) for c in remaining.values() if len(c)==1)
  if any(not c for c in remaining.values()):return assigned,None,set()
  while queue:
   lit,deps=queue.popleft();var=abs(lit)
   if var in assigned:
    if assigned[var]!=(lit>0):return assigned,None,deps|dependencies[var]
    continue
   assigned[var]=lit>0;dependencies[var]=deps
   for i in occ[lit]:remaining.pop(i,None)
   for i in occ[-lit]:
    if i not in remaining:continue
    remaining[i]=tuple(x for x in remaining[i] if x!=-lit)
    if not remaining[i]:return assigned,None,causes(i)
    if len(remaining[i])==1:
     x=remaining[i][0];queue.append((x,causes(i,abs(x))))
  return assigned,list(remaining.values()),None
 while True:
  visited+=1
  if visited>max_nodes:status='UNKNOWN_SEARCH_LIMIT';model=None;break
  assigned,residual,core=propagate()
  if residual is None:
   clause=[-lit for lit in decisions if lit in core];assert len(clause)==len(core)
   index=len(database);database.append(tuple(clause));learned.append(clause)
   for lit in clause:occ[lit].add(index)
   if not clause:status='UNSAT';model=None;break
   levels=[i+1 for i,lit in enumerate(decisions) if lit in core];target=sorted(levels)[-2] if len(levels)>1 else 0
   distance=len(decisions)-target
   if distance>1:backjumps+=1;skipped+=distance-1
   decisions=decisions[:target];continue
  if not residual:status='SAT';model={v:assigned.get(v,False) for v in range(1,variables+1)};break
  signs=defaultdict(set)
  for clause in residual:
   for literal in clause:signs[abs(literal)].add(literal)
  pure=[next(iter(signs[var])) for var in sorted(signs) if len(signs[var])==1]
  if pure:
   decisions.extend(pure);pure_batches+=1;pure_literals+=len(pure)
  else:
   shortest=min(map(len,residual));counts=Counter(abs(x) for c in residual if len(c)==shortest for x in c);var=min(counts,key=lambda v:(-counts[v],v));decisions.append(var);ordinary_literals+=1
 return dict(status=status,visited_nodes=visited,model=model,rup_additions=learned,nonchronological_backjumps=backjumps,skipped_levels=skipped,pure_literal_batches=pure_batches,pure_decision_literals=pure_literals,ordinary_decision_literals=ordinary_literals,counter_semantics="visited_nodes counts propagation rounds; one pure batch may add many ordinary signed decision levels")
