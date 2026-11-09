"""Independent signed-path oracle for potential union and conflict detection."""
import json,random,sys
from pathlib import Path
from collections import deque
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from exact_arc_potential_v1 import Potentials
checked=0
for seed in range(200):
 rng=random.Random(seed);n=rng.randint(2,40);graph=[[] for _ in range(n)];uf=Potentials(n)
 for step in range(100):
  u=rng.randrange(n);v=rng.randrange(n);cost=rng.randrange(-5,6)*(1<<70)+rng.randrange(-3,4)
  todo=deque([u]);values={u:0}
  while todo and v not in values:
   x=todo.popleft()
   for y,delta in graph[x]:
    if y not in values:values[y]=values[x]+delta;todo.append(y)
  expected='merged' if v not in values else 'consistent' if values[v]==cost else 'conflict'
  assert uf.constrain(u,v,cost)==expected
  if expected=='merged':graph[u].append((v,cost));graph[v].append((u,-cost))
  if expected!='conflict':
   a,du=uf.find(u);b,dv=uf.find(v);assert a==b and dv-du==cost
  checked+=1
D=R/'experiments/exact_arc_potential_contract_v1_2026-10-08';D.mkdir(exist_ok=False)
bindings={str(p):sha(p) for p in [Path(__file__),R/'tools/exact_arc_potential_v1.py']}
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,graphs=200,constraint_operations=checked,independent_forest_signed_path_and_union_conflict_checks_pass=True,scope='Exact arbitrary signed >64bit constraints, self-loops, disconnected components and post-conflict recovery; no real RR all-arc or endpoint reachability proof.'),indent=2)+'\n')
print('PASS potential constraints',checked)
