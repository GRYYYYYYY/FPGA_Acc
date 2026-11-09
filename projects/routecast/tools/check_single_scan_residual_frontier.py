"""Independent repeated-relaxation closure and boundary fixtures."""
import json,random
from pathlib import Path
from single_scan_residual_frontier import residual_reachability
from pre_route_endpoints import sha
rng=random.Random(20261007);cases=0
for n in range(1,51):
 for trial in range(20):
  edges=[(rng.randrange(n),rng.randrange(n)) for _ in range(rng.randrange(5*n+1))];capacities=[rng.randrange(4) for _ in range(n)];other={u:rng.randrange(5) for u in range(n)};source=rng.randrange(n);rows=[0];dest=[]
  for u in range(n):dest.extend(v for a,v in edges if a==u);rows.append(len(dest))
  fields=dict(row_offsets=rows,dest_ranks=dest,capacities=capacities)
  expected={source} if other.get(source,0)<capacities[source] else set()
  while True:
   expanded=expected|{v for u,v in edges if u in expected and other.get(v,0)<capacities[v]}
   if expanded==expected:break
   expected=expanded
  boundary=sorted({v for u,v in edges if u in expected and v not in expected}) if expected else [source]
  before=(list(rows),list(dest),list(capacities),dict(other));assert residual_reachability(fields,source,other)==(expected,boundary);assert before==(rows,dest,capacities,other);cases+=1
root=Path(__file__).resolve().parents[1];out=root/'experiments/single_scan_residual_frontier_contract_2026-10-07';out.mkdir(exist_ok=True);(out/'verification.json').write_text(json.dumps(dict(cases=cases,seed=20261007,source_sha256=sha(Path(__file__)),helper_sha256=sha(root/'tools/single_scan_residual_frontier.py'),scope='1000 directed multigraph fixtures, independent repeated-relaxation closure and edge-set boundary, zero capacities/blocked sources/cycles/parallel edges and input nonmutation. Static capacities/demand throughout traversal; not whole repair or native route parity.'),indent=2)+'\n');print('Verified',cases,'closure/frontier fixtures',flush=True)
