"""Exhaustive simple-path oracle including a delay/cost nondominance trap."""
import json,sys,random
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from tree_pareto_search_v1 import search
class RC:
 def __init__(self,inc):self.increments=inc
f=dict(row_offsets=[0,2,3,4,5,5],dest_ranks=[1,2,3,3,4],edge_ids=list(range(5)),capacities=[1]*5);rc=RC([1,4,1,1,3]);spans=[0,10,0,0,0];r=search(f,rc,0,4,{0:0},{0},{},6,spans,1);assert r['status']=='FOUND' and r['physical_edge_ids']==[0,2,4] and r['cost']==15 and r['delay']==5
r=search(f,rc,0,4,{0:0,1:1,3:2},{0,1,3},{0:1,1:1,3:1},6,spans,1);assert r['join']==3 and r['physical_edge_ids']==[4] and r['cost']==5
assert search(f,rc,0,4,{0:0},{0},{},6,spans,1,max_labels=1)['status']=='LABEL_LIMIT'
rng=random.Random(11);count=0
for trial in range(100):
 n=6;arcs=[(u,v,rng.randrange(1,5)) for u in range(n) for v in range(u+1,n) if rng.random()<.4];offset=[0];dest=[];inc=[]
 for u in range(n):
  for a,v,d in arcs:
   if a==u:dest.append(v);inc.append(d)
  offset.append(len(dest))
 f=dict(row_offsets=offset,dest_ranks=dest,edge_ids=list(range(len(dest))),capacities=[1]*n);spans=[rng.randrange(4) for _ in range(n)];budget=rng.randrange(1,15);penalty=rng.randrange(4);options=[]
 def visit(u,delay,cost,path):
  if delay>budget:return
  if u==n-1:options.append((cost,delay,path));return
  for s in range(offset[u],offset[u+1]):v=dest[s];visit(v,delay+inc[s],cost+inc[s]+penalty*spans[v],path+[s])
 visit(0,0,0,[]);r=search(f,RC(inc),0,n-1,{0:0},{0},{},budget,spans,penalty)
 if options:
  best=min((cost,d) for cost,d,path in options);assert r['status']=='FOUND' and (r['cost'],r['delay'])==best
 else:assert r['status']=='NO_BUDGET_CAPACITY_PATH'
 count+=1
out=R/'experiments/tree_pareto_search_contract_v1_2026-10-07';out.mkdir();(out/'receipt.json').write_text(json.dumps(dict(nondominated_delay_cost_trap_pass=True,retained_prefix_zero_new_wire_pass=True,label_limit_pass=True,exhaustive_dag_cases=count,bindings={str(Path(__file__)):sha(__file__),str(R/'tools/tree_pareto_search_v1.py'):sha(R/'tools/tree_pareto_search_v1.py')},scope='Small explicit and random DAG exhaustive simple-path minimum cost/delay oracle; no arbitrary cyclic RR/native STA claim.'),indent=2)+'\n');print('PASS',count)
