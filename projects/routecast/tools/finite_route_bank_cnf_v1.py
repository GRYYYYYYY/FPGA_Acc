"""Exact Boolean finite-bank encoding: one path per CID, unique NET capacities, parents."""
from collections import defaultdict
from itertools import combinations

def encode(bank,queries,capacities):
 variables=[];clauses=set()
 def var(kind,key):variables.append(dict(kind=kind,key=key));return len(variables)
 def clause(*lits):clauses.add(tuple(sorted(set(lits))))
 def atmost(xs,k,group):
  if len(xs)<=k:return
  if k==0:
   for x in xs:clause(-x)
   return
  if k==1:
   for a,b in combinations(xs,2):clause(-a,-b)
   return
  previous={}
  for i,x in enumerate(xs):
   current={j:var('PREFIX_COUNT',[group,i,j]) for j in range(1,min(k,i+1)+1)};clause(-x,current[1])
   for j,v in previous.items():clause(-v,current[j])
   for j in range(2,min(k,i+1)+1):clause(-x,-previous[j-1],current[j])
   if k in previous:clause(-x,-previous[k])
   previous=current
 path_vars={};node_users=defaultdict(lambda:defaultdict(set));parent_users=defaultdict(lambda:defaultdict(set))
 for cid,opts in sorted(bank.items()):
  xs=[]
  for index,option in enumerate(opts):
   x=var('PATH',[cid,index]);path_vars[cid,index]=x;xs.append(x);net=queries[cid]['net_id'];path=option['path']
   for n,s in path:node_users[n][net].add(x)
   for (u,_),(n,s) in zip(path,path[1:]):parent_users[net,n][u,s].add(x)
  clause(*xs);atmost(xs,1,['CID',cid])
 for n,users in sorted(node_users.items()):
  if len(users)<=capacities[n]:continue
  xs=[]
  for net,paths in sorted(users.items()):
   z=var('NET_NODE',[net,n]);xs.append(z)
   for x in paths:clause(-x,z)
  atmost(xs,capacities[n],['CAPACITY',n])
 for (net,n),parents in sorted(parent_users.items()):
  if len(parents)<2:continue
  xs=[]
  for (u,s),paths in sorted(parents.items()):
   y=var('NET_PARENT',[net,n,u,s]);xs.append(y)
   for x in paths:clause(-x,y)
  atmost(xs,1,['PARENT',net,n])
 return dict(variables=variables,clauses=[list(c) for c in sorted(clauses)],path_vars={f'{c}:{i}':x for (c,i),x in path_vars.items()},scope='Boolean formulation only, not SAT solver output or feasibility proof. Capacity counts distinct NETs, including higher-order k; shared-parent uniqueness encoded separately.')
