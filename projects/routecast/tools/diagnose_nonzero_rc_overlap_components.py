"""Conservative candidate resource overlap connectivity (not a UNSAT proof)."""
import json
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];parent=root/'experiments/nonzero_rc_multi_context_2026-10-06';r=json.loads((parent/'receipt.json').read_text());groups=r['candidates'];owners=defaultdict(set)
for i,g in enumerate(groups):
 for p in g['paths']:
  for n in p['nodes']:owners[n].add(i)
adj=[set() for _ in groups]
for ids in owners.values():
 for i in ids:adj[i].update(ids-{i})
remaining=set(range(len(groups)));components=[]
while remaining:
 pending=[min(remaining)];seen=set(pending)
 while pending:
  for j in adj[pending.pop()]-seen:seen.add(j);pending.append(j)
 remaining-=seen;components.append([groups[i]['key'] for i in sorted(seen)])
out=root/'experiments/nonzero_rc_degree_selection_2026-10-06';assert out.is_dir();(out/'overlap_components.json').write_text(json.dumps({'components':components,'component_sizes':list(map(len,components)),'pool_sha256':sha(parent/'receipt.json'),'scope':'Connect all shared candidate nodes regardless of capacity or same NET; conservative decomposition check only, one component does not preclude finer constraint-specific decomposition.'},indent=2)+'\n');print('component sizes',list(map(len,components)))
