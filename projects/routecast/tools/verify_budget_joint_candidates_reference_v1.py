"""Independent Cartesian product / original edge-table oracle."""
import itertools,json,random,hashlib
from pathlib import Path
from budget_joint_candidates_reference_v1 import select

def paths(adj,u,s,seen):
 if u==s:
  yield []; return
 for e,v,r,p in adj[u]:
  if v not in seen:
   for suffix in paths(adj,v,s,seen|{v}): yield [e]+suffix

def oracle(adj,budgets,candidates):
 edges={e:(u,v,r,p) for u,arcs in adj.items() for e,v,r,p in arcs}; best=None
 for combo in itertools.product(*(candidates[s] for s in sorted(budgets))):
  parents={}; union=set(); good=True
  for s,path in zip(sorted(budgets),combo):
   u=0; delay=0; seen={0}
   for e in path:
    a,v,r,p=edges[e]
    if a!=u or v in seen or (v in parents and parents[v]!=e): good=False; break
    parents[v]=e;union.add(e);seen.add(v);u=v;delay+=r
   if u!=s or delay>budgets[s]:good=False
  if good:
   value=sum(edges[e][2]+edges[e][3] for e in union)
   best=value if best is None else min(best,value)
 return best
cases=0
for seed in range(150):
 rng=random.Random(seed);adj={u:[] for u in range(5)};eid=0
 for u in adj:
  for v in adj:
   if u!=v and rng.random()<.35:
    adj[u].append((eid,v,rng.randrange(5),rng.randrange(6)));eid+=1
 candidates={s:list(paths(adj,0,s,{0})) for s in (3,4)}
 for b in (2,5,12):
  budgets={3:b,4:b+1}; expected=oracle(adj,budgets,candidates); actual=select(adj,0,budgets,candidates)
  assert actual['union_cost']==expected,(seed,b,actual,expected)
  assert actual['status']==('NO_COMPATIBLE_CANDIDATE_COMBINATION' if expected is None else 'OPTIMAL_WITHIN_CANDIDATES')
  if expected is not None:assert oracle(adj,budgets,{s:[p] for s,p in actual['paths'].items()})==expected
  cases+=1
adj={0:[(0,1,5,0),(1,2,1,10)],1:[(2,3,0,0)],2:[(3,3,0,0)],3:[(4,4,0,0),(5,5,5,0)],4:[],5:[]}
candidates={s:list(paths(adj,0,s,{0})) for s in (4,5)}
a=select(adj,0,{4:10,5:7},candidates)
assert a['paths']=={4:[1,3,4],5:[1,3,5]} and a['union_cost']==16
assert select(adj,0,{4:10,5:7},candidates,max_states=1)['status']=='UNKNOWN_STATE_LIMIT'
root=Path(__file__).resolve().parents[1];out=root/'experiments/budget_joint_candidates_reference_v1_2026-10-09';out.mkdir(exist_ok=False)
files=[Path(__file__),root/'tools/budget_joint_candidates_reference_v1.py',root/'tools/budget_NET_gate_reference_v1.py']
r=dict(all_pass=True,exhaustive_joint_cases=cases,conflict_recovery=a,state_limit_unknown=True,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},scope='Complete simple path sets on small graphs only. Union-edge objective defined for reference; not original model equivalence, full RR scalability or native gain.')
(out/'verification.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
