"""Verify shared-edge charging and greedy per-step optima independently."""
import copy,hashlib,json,random
from pathlib import Path
from shared_tree_budget_repair_implicit import repair

def main():
 nodes=[(0,1,0),(1,3,0),(4,0,0),(4,0,0),(4,0,0)]
 edges=[(1,0,1),(2,0,1),(3,0,1),(4,0,1)];die=[0,1,1,1,0];length=[0,1,1,1,1]
 tasks=[dict(id=i,sink=v,delay_budget=10,max_hops=10) for i,v in enumerate([2,3])]
 result=repair(nodes,edges,[True]*5,length,die,0,tasks,1)
 assert result['complete'] and result['crossings']==1
 assert [v['search']['crossings'] for v in result['steps']]==[1,0]
 frozen=copy.deepcopy(tasks);bad=repair(nodes,edges,[True]*5,length,die,0,tasks+[dict(id=2,sink=4,delay_budget=10,max_hops=10)],1)
 assert not bad['complete'] and not bad['published'] and tasks==frozen
 assert repair(nodes,edges,[True]*5,length,die,0,tasks,1,maximum_labels=1)['status']=='label_budget_exhausted'
 rng=random.Random(18102026);cases=400
 for case in range(cases):
  n=6;nodes=[];edges=[];adj=[]
  for u in range(n):
   row=[(v,rng.randrange(4)) for v in range(n) if u!=v and rng.random()<0.35]
   nodes.append((len(edges),len(row),0));edges.extend((v,0,w) for v,w in row);adj.append(row)
  die=[rng.randrange(3) for _ in range(n)];length=[rng.randrange(4) for _ in range(n)];allowed=[True]+[bool(rng.randrange(4)) for _ in range(n-1)]
  tasks=[dict(id=i,sink=v,delay_budget=rng.randrange(12),max_hops=6) for i,v in enumerate([4,5])];budget=rng.randrange(5)
  result=repair(nodes,edges,allowed,length,die,0,tasks,budget);parent={};failed=False
  for task,step in zip(tasks,result['steps']):
   prefix=parent.copy();used=sum(die[v]!=die[u] for v,u in prefix.items());best=None
   def walk(path,delay):
    nonlocal best
    if delay>task['delay_budget']:return
    u=path[-1]
    if u==task['sink']:
     incremental_wire=sum(length[v] for v in path[1:] if v not in prefix)
     incremental_cross=sum(die[a]!=die[b] for a,b in zip(path,path[1:]) if b not in prefix)
     if used+incremental_cross<=budget:
      value=(incremental_wire,delay,incremental_cross);best=value if best is None else min(best,value)
     return
    for v,w in adj[u]:
     if allowed[v] and v not in path and (v not in prefix or prefix[v]==u):walk(path+[v],delay+w)
   if allowed[0] and allowed[task['sink']]:walk([0],0)
   answer=step['search'];assert (answer['status']=='optimal_path')==(best is not None),(case,best,answer)
   if best is None:failed=True;break
   assert (answer['wire'],answer['delay'],answer['crossings'])==best
   for u,v in zip(answer['path_nodes'],answer['path_nodes'][1:]):parent[v]=u
  assert result['complete']==(not failed)
  if result['complete']:assert result['parent']==parent and result['crossings']<=budget
 root=Path(__file__).resolve().parents[1];out=root/'work/implicit_tree_budget_oracle_checks_20261017';out.mkdir(exist_ok=False)
 files=[Path(__file__).resolve(),Path(__file__).with_name('shared_tree_budget_repair_implicit.py'),Path(__file__).with_name('implicit_tree_budget_search.py')]
 report=dict(status='implicit_shared_crossing_partial_failure_and400_exhaustive_oracles_pass',random_graphs=cases,source_sha256={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},adopted=False,research_complete=False,
  scope='Per-step fixed-prefix optimum and incremental shared tree accounting; no globalSteiner optimality/nativegraph/globalSTA/devicepublication proof.')
 (out/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
