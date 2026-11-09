"""Independent Floyd-Warshall oracle including zero-delay and disabled nodes."""
import random,json
from pathlib import Path
from pre_route_endpoints import sha
from static_budget_reachability import within_budget
rng=random.Random(41);checks=0
for trial in range(120):
 n=rng.randrange(2,15);caps=[rng.randrange(3) for _ in range(n)];rows=[0];dest=[];inc=[];matrix=[[None]*n for _ in range(n)]
 for u in range(n):
  if caps[u]>0:matrix[u][u]=0
  for v in range(n):
   if rng.random()<.2:
    w=rng.randrange(10);dest.append(v);inc.append(w)
    if caps[u]>0 and caps[v]>0 and (matrix[u][v] is None or w<matrix[u][v]):matrix[u][v]=w
  rows.append(len(dest))
 for k in range(n):
  for u in range(n):
   for v in range(n):
    if matrix[u][k] is not None and matrix[k][v] is not None:
     value=matrix[u][k]+matrix[k][v]
     if matrix[u][v] is None or value<matrix[u][v]:matrix[u][v]=value
 for source in range(n):
  initial=rng.randrange(5);budget=rng.randrange(20);a=within_budget(rows,dest,inc,caps,source,initial,budget,range(n))
  for target in range(n):
   value=matrix[source][target];expected=initial+value if value is not None and initial+value<=budget else None;assert a['target_minima'][target]==expected;checks+=1
p=Path(__file__).resolve().parents[1]/'experiments/static_budget_reachability_contract_2026-10-07';p.mkdir();(p/'verification.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),implementation_sha256=sha(Path(__file__).with_name('static_budget_reachability.py')),floyd_warshall_comparisons=checks,graphs=120,scope='Small integer graphs with positive/zero delays, disabled nodes, SOURCE initial and cap boundary. No perNET occupancy or production timing proof.'),indent=2)+'\n');print(checks)
