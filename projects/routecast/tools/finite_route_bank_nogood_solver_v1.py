"""Finite-domain exhaustive DFS with forced assignments and explicit proof tree."""
from collections import Counter,defaultdict
class Limit(Exception):pass
def solve(bank,queries,capacities,max_nodes=100000):
 assigned={};uses=defaultdict(Counter);parents=defaultdict(dict);parent_uses=defaultdict(Counter);owners=Counter();visited=0;nogoods=[];learned=set();nogood_hits=0
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
 def learn(failed):
  relevant={n for option in bank[failed] for n,s in option['path']}
  selected={c:i for c,i in assigned.items() if relevant&{n for n,s in bank[c][i]['path']}}
  def blocked(subset):
   occupancy=defaultdict(set);ps=defaultdict(dict)
   for c,i in subset.items():
    net=queries[c]['net_id'];path=bank[c][i]['path']
    for n,s in path:occupancy[n].add(net)
    for (u,_),(v,s) in zip(path,path[1:]):ps[net][v]=(u,s)
   net=queries[failed]['net_id']
   return all(any(len(occupancy[n]|{net})>capacities[n] for n,s in option['path']) or any(v in ps[net] and ps[net][v]!=(u,s) for (u,_),(v,s) in zip(option['path'],option['path'][1:])) for option in bank[failed])
  assert blocked(selected)
  for c in sorted(list(selected)):
   reduced={cid:i for cid,i in selected.items() if cid!=c}
   if blocked(reduced):selected=reduced
  key=(failed,tuple(sorted(selected.items())))
  if key not in learned:learned.add(key);nogoods.append(key)
 def dfs():
  nonlocal visited,nogood_hits
  visited+=1
  if visited>max_nodes:raise Limit()
  proof={'forced':[]}
  while len(assigned)<len(bank):
   hit=next((failed for failed,core in nogoods if failed not in assigned and all(assigned.get(c)==i for c,i in core)),None)
   if hit is not None:
    assert all(not legal(hit,i) for i in range(len(bank[hit])));nogood_hits+=1;proof.update(kind='DEAD',empty_connection=hit)
    for c,i in reversed(proof['forced']):remove(c)
    return False,proof
   domains={cid:[i for i in range(len(options)) if legal(cid,i)] for cid,options in bank.items() if cid not in assigned}
   cid=min(domains,key=lambda c:(len(domains[c]),c));options=domains[cid]
   if not options:
    learn(cid)
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
  success,proof=dfs();return dict(status='FOUND' if success else 'FINITE_BANK_EXHAUSTED',visited_nodes=visited,learned_nogoods=len(nogoods),nogood_hits=nogood_hits,proof=proof,selection=dict(assigned) if success else None)
 except Limit:return dict(status='SEARCH_LIMIT',visited_nodes=visited,learned_nogoods=len(nogoods),nogood_hits=nogood_hits,proof=None,selection=None)
