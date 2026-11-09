"""Independent exhaustive boundary coverage, including zero-weight cycles."""
import hashlib,json,random
from pathlib import Path
from single_owner_exchange_search import search

def main():
 rng=random.Random(15302026);cases=2000;zero_cases=0;no_path=0;non_simple=0
 for case in range(cases):
  n=6;adj=[[] for _ in range(n)];nodes=[];edges=[]
  for u in range(n):
   for v in range(n):
    if u!=v and rng.random()<0.3:adj[u].append((v,rng.randrange(5)))
   nodes.append((len(edges),len(adj[u]),0));edges.extend((v,0,w) for v,w in adj[u])
  members=[set(rng.sample(range(5),rng.randrange(5))) for _ in range(n)]
  members[0]=set();capacities=[1]+[rng.randrange(4) for _ in range(n-1)]
  bound=rng.randrange(11);best=None
  def enumerate_paths(path,cost):
   nonlocal best
   if cost>bound:return
   if path[-1]==n-1:
    for released in [None,0,1,2,3]:
     if all(len(members[v]-{4}-{released})<capacities[v] for v in path):
      best=cost if best is None else min(best,cost)
    return
   for v,w in adj[path[-1]]:
    if v not in path:enumerate_paths(path+[v],cost+w)
  enumerate_paths([0],0)
  result=search(nodes,edges,capacities,members,0,n-1,4,bound)
  assert result['found']==(best is not None),(case,result,best)
  zero_cases+=any(w==0 for _,_,w in edges)
  if best is None:no_path+=1;continue
  assert result['delay']==best
  path=result['path_nodes'];release=result['released_owner']
  assert all(len(members[v]-{4}-{release})<capacities[v] for v in path)
  assert sum(edges[e][2] for e in result['path_edges'])==best
  for u,v,e in zip(path,path[1:],result['path_edges']):
   begin,count,_=nodes[u];assert begin<=e<begin+count and edges[e][0]==v
  non_simple+=len(set(path))!=len(path)
 # Empty path, zero budget, and precondition rejection.
 assert search([(0,0,0)],[],[1],[set()],0,0,4,0)['path_nodes']==[0]
 for capacities,members in [([0],[set()]),([1],[{2}])]:
  try:search([(0,0,0)],[],capacities,members,0,0,4,0)
  except ValueError:pass
  else:raise AssertionError('occupied/zero-capacity source accepted')
 root=Path(__file__).resolve().parents[1];out=root/'work/single_owner_exchange_boundary_checks_20261015';out.mkdir(exist_ok=False)
 files=[Path(__file__).resolve(),Path(__file__).with_name('single_owner_exchange_search.py')]
 audit=dict(status='2000_zero_weight_capacity_and_budget_graphs_match_exhaustive_simple_path_optima',cases=cases,
  zero_weight_graphs=zero_cases,no_feasible_path_cases=no_path,returned_non_simple_paths=non_simple,
  source_sha256={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},adopted=False,research_complete=False,
  scope='Small graph exact delay/owner-capacity comparison; validates zero cycles, zero capacity, overfull resources, target ownership, zero/insufficient budgets and source preconditions. No hop/corridor/native QoR or transaction proof.')
 (out/'audit.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(audit))
if __name__=='__main__':main()
