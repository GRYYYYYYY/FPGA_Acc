"""Differential tests of implicit filtering including label-limit behavior."""
import copy,hashlib,json,random,time
from pathlib import Path
from shared_tree_budget_repair import repair as reference
from shared_tree_budget_repair_implicit import repair as candidate

def normalized(result):
 r=copy.deepcopy(result)
 for step in r['steps']:step['search'].pop('path_edges',None)
 return r

def main():
 rng=random.Random(17102026);comparisons=0;status={}
 for case in range(2400):
  n=rng.randrange(2,13);nodes=[];edges=[]
  for u in range(n):
   row=[(v,rng.randrange(3),rng.randrange(6)) for v in range(n) if rng.random()<0.28]
   if row and case%7==0:row.append(row[0])
   nodes.append((len(edges),len(row),0));edges.extend(row)
  allowed=[rng.random()>0.18 for _ in range(n)];length=[rng.randrange(4) for _ in range(n)];dies=[rng.randrange(4) for _ in range(n)];source=rng.randrange(n)
  tasks=[dict(id=i,sink=rng.randrange(n),delay_budget=rng.randrange(25),max_hops=rng.randrange(1,n+2)) for i in range(rng.randrange(1,5))];budget=rng.randrange(8)
  for cap in [1,7,2097152]:
   args=(nodes,edges,allowed,length,dies,source,tasks,budget)
   before=copy.deepcopy(args);a=reference(*args,maximum_labels=cap);b=candidate(*args,maximum_labels=cap)
   assert args==before and normalized(a)==normalized(b),(case,cap,a,b)
   for step in b['steps']:
    search=step['search']
    if search['status']=='optimal_path':
     path=search['path_nodes'];indices=search['path_edges'];assert len(indices)==len(path)-1
     for u,v,i in zip(path,path[1:],indices):
      begin,count,*_=nodes[u];assert begin<=i<begin+count and edges[i][0]==v
   comparisons+=1;status[b['status']]=status.get(b['status'],0)+1
 R=Path(__file__).resolve().parents[1];P=R/'work/implicit_tree_budget_checks_20261017';P.mkdir(exist_ok=False)
 files=[Path(__file__),*[R/'tools'/f for f in ['shared_tree_budget_repair.py','shared_tree_budget_repair_implicit.py','delay_crossing_bounded_wire_search.py','implicit_tree_budget_search.py']]]
 report=dict(status='implicit_filter_7200_differential_comparisons_pass',graphs=2400,comparisons=comparisons,status_counts=status,source_sha256={str(f.resolve()):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},scope='Exact normalized outputs including labels, expansions and path nodes; original CSR path-edge indices validated separately. No native workload runtime or quality adoption established.',adopted=False,research_complete=False)
 (P/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
