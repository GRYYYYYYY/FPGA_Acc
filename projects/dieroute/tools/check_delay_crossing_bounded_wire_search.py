"""Exhaustive checks for joint delay/crossing-budget native-length search."""
import hashlib,json,random
from pathlib import Path
from delay_crossing_bounded_wire_search import search

def main():
 rng=random.Random(20261017);no_path=0
 for case in range(1500):
  n=6;nodes=[];edges=[];cross=[];adj=[]
  for u in range(n):
   row=[]
   for v in range(n):
    if v!=u and rng.random()<0.3:
     delay=rng.randrange(5);c=rng.randrange(2);row.append((v,delay,c));edges.append((v,0,delay));cross.append(c)
   nodes.append((len(edges)-len(row),len(row),0));adj.append(row)
  allowed=[True]+[bool(rng.randrange(4)) for _ in range(n-2)]+[True];length=[rng.randrange(4) for _ in range(n)];cap=rng.randrange(13);cross_cap=rng.randrange(5);best=None
  def walk(path,wire,delay,c):
   nonlocal best
   if delay>cap or c>cross_cap:return
   if path[-1]==n-1:
    value=(wire,delay,c);best=value if best is None else min(best,value);return
   for v,w,k in adj[path[-1]]:
    if v not in path and allowed[v]:walk(path+[v],wire+length[v],delay+w,c+k)
  walk([0],0,0,0)
  result=search(nodes,edges,allowed,length,0,n-1,cap,cross,cross_cap)
  assert (result['status']=='optimal_path')==(best is not None),(case,best,result)
  if best is None:no_path+=1;continue
  assert (result['wire'],result['delay'],result['crossings'])==best
  assert len(set(result['path_nodes']))==len(result['path_nodes'])
  assert sum(cross[e] for e in result['path_edges'])==result['crossings']
  assert sum(edges[e][2] for e in result['path_edges'])==result['delay']
  assert sum(length[v] for v in result['path_nodes'][1:])==result['wire']
 nodes=[(0,2,0),(2,1,0),(3,1,0),(4,0,0)];edges=[(1,0,1),(2,0,3),(3,0,1),(3,0,3)];cross=[0,1,0,1]
 assert search(nodes,edges,[True]*4,[0,9,1,0],0,3,6,cross,0)['wire']==9
 assert search(nodes,edges,[True]*4,[0,9,1,0],0,3,6,cross,2)['wire']==1
 assert search(nodes,edges,[True]*4,[0,9,1,0],0,3,6,cross,2,maximum_labels=1)['status']=='label_budget_exhausted'
 root=Path(__file__).resolve().parents[1];out=root/'work/delay_crossing_bounded_wire_checks_20261015';out.mkdir(exist_ok=False)
 files=[Path(__file__).resolve(),Path(__file__).with_name('delay_crossing_bounded_wire_search.py')]
 report=dict(status='1500_joint_delay_crossing_budget_graphs_match_exhaustive_optima',cases=1500,no_path_cases=no_path,source_sha256={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},adopted=False,research_complete=False,
  scope='Small nonnegative-cost graphs,including zero delays/lengths/crossings,capacity mask,cross budget0,and label exhaustion. No nativegraph/sharedtree/globalSTA integration yet.')
 (out/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
