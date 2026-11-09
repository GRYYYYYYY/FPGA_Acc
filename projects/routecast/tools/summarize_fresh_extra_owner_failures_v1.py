"""Receipt-bound descriptive conflicts, not mathematical infeasibility evidence."""
import sys,json
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
out=R/'experiments/misex_fresh_extra_owner_joint_v1_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());bindings={**r['bindings'],**closure([Path(__file__)]),str(rp):sha(rp)};rows=[]
for attempt in r['attempts']:
 failures=Counter();splits=Counter();statuses=Counter()
 for b in attempt['branches']:
  path=out/f"attempt{attempt['index']}_branch{b['index']}"/'branch.json';assert sha(path)==r['files'][str(path)];bindings[str(path)]=sha(path);assert json.loads(path.read_text())['branch']==b;statuses[b['status']]+=1
  if 'conflict_node' in b:splits[b['conflict_node']]+=1
  for fail in b['failures'].values():
   if fail is not None:failures[(fail['query']['net_id'],fail['query']['connection_id'],fail['status'])]+=1
 rows.append(dict(index=attempt['index'],release=attempt['release'],status=attempt['status'],branches=len(attempt['branches']),branch_statuses=dict(statuses),conflict_nodes=dict(splits),failed_queries=[dict(net_id=k[0],connection_id=k[1],status=k[2],occurrences=v) for k,v in sorted(failures.items())]));print(attempt['index'],dict(splits),dict(failures),flush=True)
assert all(sha(k)==h for k,h in bindings.items());(out/'failure_summary.json').write_text(json.dumps(dict(rows=rows,bindings=bindings,scope='Saved bounded-search descriptive counts only, not exact failure minima or global infeasibility proof.'),indent=2)+'\n')
