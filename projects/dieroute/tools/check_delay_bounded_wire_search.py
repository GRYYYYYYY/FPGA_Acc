"""Exhaustively validate constrained native-length search on small graphs."""
import hashlib,json,random
from pathlib import Path
from delay_bounded_wire_search import search

def main():
 rng=random.Random(20261016);total=1000;no_path=0
 for case in range(total):
  n=6;nodes=[];edges=[];adj=[]
  for u in range(n):
   row=[(v,rng.randrange(5)) for v in range(n) if v!=u and rng.random()<0.3]
   adj.append(row);nodes.append((len(edges),len(row),0));edges.extend((v,0,w) for v,w in row)
  allowed=[True]+[bool(rng.randrange(4)) for _ in range(n-2)]+[True]
  lengths=[rng.randrange(4) for _ in range(n)];budget=rng.randrange(13);best=None
  def walk(path,wire,delay):
   nonlocal best
   if delay>budget:return
   if path[-1]==n-1:
    value=(wire,delay);best=value if best is None else min(best,value);return
   for v,w in adj[path[-1]]:
    if allowed[v] and v not in path:walk(path+[v],wire+lengths[v],delay+w)
  walk([0],0,0)
  result=search(nodes,edges,allowed,lengths,0,n-1,budget)
  assert (result['status']=='optimal_path')==(best is not None),(case,best,result)
  if best is None:no_path+=1;continue
  assert (result['wire'],result['delay'])==best,(case,best,result)
  path=result['path_nodes'];assert path[0]==0 and path[-1]==n-1
  assert len(set(path))==len(path)
  assert sum(lengths[v] for v in path[1:])==result['wire']
  assert sum(edges[i][2] for i in result['path_edges'])==result['delay']
  for u,v,i in zip(path,path[1:],result['path_edges']):
   begin,count,_=nodes[u];assert begin<=i<begin+count and edges[i][0]==v
 # Fast path exceeds cap; slower short wire path is the exact feasible answer.
 nodes=[(0,2,0),(2,1,0),(3,1,0),(4,0,0)];edges=[(1,0,1),(2,0,3),(3,0,1),(3,0,3)]
 assert search(nodes,edges,[True]*4,[0,9,1,0],0,3,5)['wire']==9
 assert search(nodes,edges,[True]*4,[0,9,1,0],0,3,6)['wire']==1
 assert search(nodes,edges,[True]*4,[0,9,1,0],0,3,6,maximum_labels=1)['status']=='label_budget_exhausted'
 root=Path(__file__).resolve().parents[1];out=root/'work/delay_bounded_wire_search_checks_20261015';out.mkdir(exist_ok=False)
 files=[Path(__file__).resolve(),Path(__file__).with_name('delay_bounded_wire_search.py')]
 report=dict(status='1000_exhaustive_delay_bounded_wire_graphs_and_exhaustion_controls_pass',cases=total,no_path_cases=no_path,
  source_sha256={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},adopted=False,research_complete=False,
  scope='Additive nonnegative native lengths and edge delays on small graphs; zero costs, allowed masks,delay caps and label exhaustion. No full-net sharing/hop bound/policy integration/global native QoR proof.')
 (out/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
