"""Independent role and clause reconstruction on supplied original path bank."""
import json
from collections import defaultdict
from itertools import combinations
def verify_encoding(encoded,bank,q,inv):
 roles={}
 for i,role in enumerate(encoded['variables'],1):
  key=(role['kind'],json.dumps(role['key']));assert key not in roles;roles[key]=i
 used=set();expected=set();groups=defaultdict(int)
 def v(kind,key):
  var=roles[kind,json.dumps(key)];used.add(var);return var
 def emit(literals):expected.add(tuple(sorted(set(literals))))
 def cardinality(xs,k,group):
  if len(xs)<=k:return
  groups[group[0]]+=1
  if k==0:
   for x in xs:emit([-x])
  elif k==1:
   for a,b in combinations(xs,2):emit([-a,-b])
  else:
   for i,x in enumerate(xs):
    emit([-x,v('PREFIX_COUNT',[group,i,1])])
    for count in range(1,min(i,k)+1):emit([-v('PREFIX_COUNT',[group,i-1,count]),v('PREFIX_COUNT',[group,i,count])])
    for count in range(2,min(i+1,k)+1):emit([-x,-v('PREFIX_COUNT',[group,i-1,count-1]),v('PREFIX_COUNT',[group,i,count])])
    if i>=k:emit([-x,-v('PREFIX_COUNT',[group,i-1,k])])
 usage=defaultdict(lambda:defaultdict(set));parents=defaultdict(lambda:defaultdict(set));pathvars={}
 for cid,options in bank.items():
  xs=[]
  for i,option in enumerate(options):
   x=v('PATH',[cid,i]);pathvars[f'{cid}:{i}']=x;xs.append(x);net=q[cid]['net_id'];path=option['path']
   for n,s in path:usage[n][net].add(x)
   for (u,_),(n,s) in zip(path,path[1:]):parents[net,n][u,s].add(x)
  emit(xs);cardinality(xs,1,['CID',cid])
 for n,users in usage.items():
  cap=int(inv.physical.nodes[n][1])
  if len(users)<=cap:continue
  xs=[]
  for net in sorted(users):
   z=v('NET_NODE',[net,n]);xs.append(z)
   for x in users[net]:emit([-x,z])
  cardinality(xs,cap,['CAPACITY',n])
 for (net,n),options in parents.items():
  if len(options)<2:continue
  xs=[]
  for u,s in sorted(options):
   y=v('NET_PARENT',[net,n,u,s]);xs.append(y)
   for x in options[u,s]:emit([-x,y])
  cardinality(xs,1,['PARENT',net,n])
 assert pathvars==encoded['path_vars'];assert used==set(range(1,len(encoded['variables'])+1));assert expected=={tuple(c) for c in encoded['clauses']} and len(expected)==len(encoded['clauses'])
 return True
