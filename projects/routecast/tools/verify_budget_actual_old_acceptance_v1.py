"""Independent edge-table oracle, randomized feasible old trees and cap fallback."""
import copy,hashlib,itertools,json,random
from pathlib import Path
from budget_actual_old_acceptance_v1 import choose

def paths(adj,u,s,seen):
 if u==s:yield [];return
 for e,v,r,p in adj[u]:
  if v not in seen:
   for suffix in paths(adj,v,s,seen|{v}):yield [e]+suffix

def oracle(edges,budgets,chosen):
 parents={};union=set()
 for s,path in chosen.items():
  u=0;seen={0};raw=0
  for e in path:
   a,v,r,p=edges[e]
   if a!=u or v in seen or (v in parents and parents[v]!=e):return None
   parents[v]=e;union.add(e);raw+=r;u=v;seen.add(v)
  if u!=s or raw>budgets[s]:return None
 return sum(edges[e][2]+edges[e][3] for e in union)

cases=0;feasible_graphs=0
for seed in range(150):
 rng=random.Random(seed);adj={u:[] for u in range(5)};eid=0
 for u in adj:
  for v in adj:
   if u!=v and rng.random()<.35:adj[u].append((eid,v,rng.randrange(5),rng.randrange(6)));eid+=1
 edges={e:(u,v,r,p) for u,arcs in adj.items() for e,v,r,p in arcs};budgets={3:8,4:9}
 candidates={s:list(paths(adj,0,s,{0})) for s in budgets};legal=[]
 for combo in itertools.product(*(candidates[s] for s in budgets)):
  tree=dict(zip(budgets,combo));cost=oracle(edges,budgets,tree)
  if cost is not None:legal.append((cost,tree))
 if not legal:continue
 feasible_graphs+=1;old_cost,old=max(legal,key=lambda x:x[0]);before=copy.deepcopy((adj,budgets,old,candidates))
 for cap in (1,3,10000):
  result=choose(adj,0,budgets,old,candidates,max_states=cap)
  chosen_cost=oracle(edges,budgets,result['paths']);assert chosen_cost is not None and chosen_cost==result['chosen_union_cost']<=old_cost
  assert result['old_union_cost']==old_cost and (adj,budgets,old,candidates)==before
  if result['status']=='RETAIN':assert result['paths']==old
  else:assert chosen_cost<old_cost
  if cap==10000:assert chosen_cost==min(x[0] for x in legal)
  cases+=1
# Candidate set omits a better current old path: it must stay available.
adj={0:[(0,1,1,0),(1,1,5,5)]};old={1:[0]}
for cap in (1,10):
 result=choose(adj,0,{1:10},old,{1:[[1]]},max_states=cap)
 assert result['status']=='RETAIN' and result['paths']==old and result['chosen_union_cost']==1
root=Path(__file__).resolve().parents[1];out=root/'experiments/budget_actual_old_acceptance_v1_2026-10-09';out.mkdir(exist_ok=False)
files=[Path(__file__),root/'tools/budget_actual_old_acceptance_v1.py',root/'tools/budget_joint_candidates_incremental_v2.py',root/'tools/budget_NET_gate_reference_v1.py']
r=dict(all_pass=True,feasible_random_graphs=feasible_graphs,random_old_tree_limit_cases=cases,omitted_actual_old_regression_prevented=True,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},scope='Small graph actual-old admission safety; not production query/RC adapter, epoch/ledger commit, original RR quality or full workflow gains.')
(out/'verification.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
