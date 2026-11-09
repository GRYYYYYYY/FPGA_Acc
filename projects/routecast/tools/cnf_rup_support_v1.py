"""RUP support extraction on explicit formula and proof, no archived artifacts."""
def support(clauses,result):
 database=list(clauses);base=len(database);graph={}
 for added in result['rup_additions']:
  values={abs(x):x<0 for x in added};reasons={abs(x):set() for x in added};support=None
  while support is None:
   changed=False
   for index,clause in enumerate(database):
    if any(abs(x) in values and values[abs(x)]==(x>0) for x in clause):continue
    residual=set(x for x in clause if abs(x) not in values)
    deps={index}.union(*(reasons[abs(x)] for x in clause if abs(x) in values))
    if not residual:support=deps;break
    if len(residual)==1:
     x=next(iter(residual));values[abs(x)]=x>0;reasons[abs(x)]=deps;changed=True
   assert support is not None or changed
  graph[len(database)]=sorted(support);database.append(added)
 assert database[-1]==[];needed=set();queue=[len(database)-1]
 while queue:
  i=queue.pop()
  if i in needed:continue
  needed.add(i)
  if i>=base:queue.extend(graph[i])
 return sorted(i for i in needed if i<base)
