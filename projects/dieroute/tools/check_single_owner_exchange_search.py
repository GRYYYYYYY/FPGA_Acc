"""Compare the augmented search against independent exhaustive simple paths."""
import hashlib,itertools,json,random
from pathlib import Path
from single_owner_exchange_search import search

def main():
 random.seed(20261015);cases=0
 for case in range(500):
  n=6;adj=[[] for _ in range(n)];nodes=[];edges=[]
  for u in range(n):
   for v in range(n):
    if u!=v and random.random()<0.25:adj[u].append((v,random.randrange(1,8)))
   nodes.append((len(edges),len(adj[u]),0));edges.extend((v,0,w) for v,w in adj[u])
  owners=[set(random.sample(range(4),random.randrange(3))) for _ in range(n)]
  owners[0]=set();capacity=[random.randrange(1,3) for _ in range(n)];target=3;bound=20
  best=None
  def walk(path,cost):
   nonlocal best
   if cost>bound:return
   u=path[-1]
   if u==n-1:
    for release in [None,0,1,2]:
     if all(len(owners[v]-{target}-{release})<capacity[v] for v in path):
      best=cost if best is None else min(best,cost)
    return
   for v,w in adj[u]:
    if v not in path:walk(path+[v],cost+w)
  walk([0],0)
  result=search(nodes,edges,capacity,owners,0,n-1,target,bound)
  assert result['found']==(best is not None),(case,result,best)
  if best is not None:
   assert result['delay']==best
   release=result['released_owner'];path=result['path_nodes']
   assert path[0]==0 and path[-1]==n-1
   assert all(len(owners[v]-{target}-{release})<capacity[v] for v in path)
   assert sum(edges[i][2] for i in result['path_edges'])==best
  cases+=1
 # One release cannot unblock two distinct owners on a chain.
 nodes=[(0,1,0),(1,1,0),(2,1,0),(3,0,0)];edges=[(1,0,1),(2,0,1),(3,0,1)]
 assert not search(nodes,edges,[1]*4,[set(),{7},{8},set()],0,3,9,10)['found']
 assert search(nodes,edges,[1,2,2,1],[set(),{7,8},{7,8},set()],0,3,9,10)['delay']==3
 root=Path(__file__).resolve().parents[1];out=root/'work/single_owner_exchange_search_checks_20261015';out.mkdir(exist_ok=False)
 files=[Path(__file__).resolve(),Path(__file__).with_name('single_owner_exchange_search.py')]
 report=dict(status='augmented_owner_search_matches500_exhaustive_graphs_and_capacity_controls',random_graphs=cases,
  source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},adopted=False,research_complete=False,
  scope='Positive-weight small graphs and explicit one-owner/capacity controls; no native graph integration, hop bounds, displaced-net repair, transaction or global QoR claim.')
 (out/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
