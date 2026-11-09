"""Occurrence-directed RUP support replay using integer bitsets for clause provenance."""
from collections import defaultdict,deque

def extract(clauses,result):
 database=[tuple(dict.fromkeys(c)) for c in clauses];base=len(database);occ=defaultdict(set);graph={}
 for i,c in enumerate(database):
  for x in c:occ[x].add(i)
 for added in result['rup_additions']:
  assigned={};reason={};remaining={i:c for i,c in enumerate(database)};queue=deque((-x,0) for x in added);queue.extend((c[0],1<<i) for i,c in remaining.items() if len(c)==1);dead=next((1<<i for i,c in remaining.items() if not c),None)
  while dead is None and queue:
   lit,deps=queue.popleft();var=abs(lit)
   if var in assigned:
    if assigned[var]!=(lit>0):dead=deps|reason[var]
    continue
   assigned[var]=lit>0;reason[var]=deps
   for i in occ[lit]:remaining.pop(i,None)
   for i in occ[-lit]:
    if i not in remaining:continue
    remaining[i]=tuple(x for x in remaining[i] if x!=-lit)
    if len(remaining[i])>1:continue
    causes=1<<i
    for x in database[i]:
     if abs(x) in assigned:causes|=reason[abs(x)]
    if not remaining[i]:dead=causes;break
    queue.append((remaining[i][0],causes))
  assert dead is not None,'Invalid RUP addition'
  index=len(database);graph[index]=dead;database.append(tuple(dict.fromkeys(added)))
  for x in database[-1]:occ[x].add(index)
 assert database[-1]==();needed=0;pending=1<<(len(database)-1)
 while pending:
  bit=pending & -pending;pending^=bit
  if needed & bit:continue
  needed|=bit;i=bit.bit_length()-1
  if i>=base:pending|=graph[i]&~needed
 originals=[i for i in range(base) if needed>>i&1];additions=[i-base for i in range(base,len(database)) if needed>>i&1]
 return dict(original_indices=originals,addition_indices=additions,clauses=[clauses[i] for i in originals],rup_additions=[result['rup_additions'][i] for i in additions])

def support(clauses,result):return extract(clauses,result)['original_indices']
