"""Finite-domain exhaustive DFS with forced assignments and explicit proof tree."""
from collections import Counter,defaultdict
class Limit(Exception):pass
def solve(bank,queries,capacities,max_nodes=100000):
 assigned={};uses=defaultdict(Counter);parents=defaultdict(dict);parent_uses=defaultdict(Counter);owners=Counter();visited=0
 def legal(cid,index):
  net=queries[cid]['net_id'];path=bank[cid][index]['path']
  return all(owners[n]-int(uses[net][n]>0)<capacities[n] for n,s in path) and all(v not in parents[net] or parents[net][v]==(u,s) for (u,_),(v,s) in zip(path,path[1:]))
 def put(cid,index):
  assigned[cid]=index;net=queries[cid]['net_id'];path=bank[cid][index]['path']
  for n,s in path:
   if uses[net][n]==0:owners[n]+=1
   uses[net][n]+=1
  for (u,_),(v,s) in zip(path,path[1:]):parents[net][v]=(u,s);parent_uses[net][v]+=1
 def remove(cid):
  net=queries[cid]['net_id'];path=bank[cid][assigned.pop(cid)]['path']
  for n,s in path:
   uses[net][n]-=1
   if uses[net][n]==0:owners[n]-=1
  for u,(v,s) in zip(path,path[1:]):
   parent_uses[net][v]-=1
   if parent_uses[net][v]==0:del parents[net][v]
 def dfs():
  nonlocal visited
  visited+=1
  if visited>max_nodes:raise Limit()
  proof={'forced':[]}
  while len(assigned)<len(bank):
   domains={cid:[i for i in range(len(options)) if legal(cid,i)] for cid,options in bank.items() if cid not in assigned}
   cid=min(domains,key=lambda c:(len(domains[c]),c));options=domains[cid]
   if not options:
    proof.update(kind='DEAD',empty_connection=cid)
    for c,i in reversed(proof['forced']):remove(c)
    return False,proof
   if len(options)>1:break
   put(cid,options[0]);proof['forced'].append([cid,options[0]])
  if len(assigned)==len(bank):proof.update(kind='SOLUTION',selection=dict(assigned));return True,proof
  proof.update(kind='BRANCH',connection=cid,children=[])
  for i in options:
   put(cid,i);success,child=dfs();proof['children'].append({'index':i,'proof':child})
   if success:return True,proof
   remove(cid)
  for c,i in reversed(proof['forced']):remove(c)
  return False,proof
 try:
  success,proof=dfs();return dict(status='FOUND' if success else 'FINITE_BANK_EXHAUSTED',visited_nodes=visited,proof=proof,selection=dict(assigned) if success else None)
 except Limit:return dict(status='SEARCH_LIMIT',visited_nodes=visited,proof=None,selection=None)
