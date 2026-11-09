"""Bounded DPLL with explicit unit/branch/conflicting-clause certificates."""
from collections import Counter
class Limit(Exception):pass

def solve(clauses,variables,max_nodes=10000):
 visited=0
 def visit(remaining,assigned):
  nonlocal visited
  visited+=1
  if visited>max_nodes:raise Limit()
  assigned=dict(assigned);proof={'forced':[]}
  while True:
   residual=[];unit=None;dead=None
   for index,clause in remaining:
    if any(abs(lit) in assigned and assigned[abs(lit)]==(lit>0) for lit in clause):continue
    reduced=tuple(lit for lit in clause if abs(lit) not in assigned)
    if not reduced:dead=index;break
    residual.append((index,reduced))
    if len(reduced)==1:unit=reduced[0]
   if dead is not None:proof.update(kind='DEAD',clause=dead);return False,proof,None
   if not residual:
    model={v:assigned.get(v,False) for v in range(1,variables+1)};proof.update(kind='SOLUTION');return True,proof,model
   if unit is None:break
   assigned[abs(unit)]=unit>0;proof['forced'].append(unit);remaining=residual
  shortest=min(len(c) for i,c in residual);counts=Counter(abs(lit) for i,c in residual if len(c)==shortest for lit in c);var=min(counts,key=lambda v:(-counts[v],v));proof.update(kind='BRANCH',variable=var,children=[])
  for value in (True,False):
   success,child,model=visit(residual,{**assigned,var:value});proof['children'].append(dict(value=value,proof=child))
   if success:return True,proof,model
  return False,proof,None
 try:
  success,proof,model=visit(list(enumerate(map(tuple,clauses))),{});return dict(status='SAT' if success else 'UNSAT',visited_nodes=visited,proof=proof,model=model)
 except Limit:return dict(status='UNKNOWN_SEARCH_LIMIT',visited_nodes=visited,proof=None,model=None)
