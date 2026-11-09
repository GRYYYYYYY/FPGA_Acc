"""Bounded DPLL with occurrence-directed unit propagation and ordinary clause proofs."""
from collections import Counter,defaultdict,deque
class Limit(Exception):pass

def solve(clauses,variables,max_nodes=10000):
 original={i:tuple(c) for i,c in enumerate(clauses)};occurrences=defaultdict(set)
 for i,c in original.items():
  for lit in c:occurrences[lit].add(i)
 visited=0
 def visit(inherited,prior,decision=None):
  nonlocal visited
  visited+=1
  if visited>max_nodes:raise Limit()
  remaining=dict(inherited);assigned=dict(prior);proof={'forced':[]};queue=deque((c[0],i) for i,c in remaining.items() if len(c)==1)
  def assign(lit,forced):
   var=abs(lit)
   if var in assigned:
    assert assigned[var]==(lit>0);return None
   assigned[var]=lit>0
   if forced:proof['forced'].append(lit)
   for i in occurrences[lit]:remaining.pop(i,None)
   for i in occurrences[-lit]:
    if i not in remaining:continue
    remaining[i]=tuple(x for x in remaining[i] if x!=-lit)
    if not remaining[i]:return i
    if len(remaining[i])==1:queue.append((remaining[i][0],i))
   return None
  dead=next((i for i,c in remaining.items() if not c),None)
  if dead is None and decision is not None:dead=assign(decision,False)
  while dead is None and queue:
   lit,i=queue.popleft()
   if i not in remaining:continue
   assert remaining[i]==(lit,);dead=assign(lit,True)
  if dead is not None:proof.update(kind='DEAD',clause=dead);return False,proof,None
  if not remaining:proof.update(kind='SOLUTION');return True,proof,{v:assigned.get(v,False) for v in range(1,variables+1)}
  shortest=min(map(len,remaining.values()));counts=Counter(abs(x) for c in remaining.values() if len(c)==shortest for x in c);var=min(counts,key=lambda v:(-counts[v],v));proof.update(kind='BRANCH',variable=var,children=[])
  for value in (True,False):
   success,child,model=visit(remaining,assigned,var if value else -var);proof['children'].append(dict(value=value,proof=child))
   if success:return True,proof,model
  return False,proof,None
 try:
  success,proof,model=visit(original,{});return dict(status='SAT' if success else 'UNSAT',visited_nodes=visited,proof=proof,model=model)
 except Limit:return dict(status='UNKNOWN_SEARCH_LIMIT',visited_nodes=visited,proof=None,model=None)
