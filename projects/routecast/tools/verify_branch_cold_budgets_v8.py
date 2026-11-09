"""Complete original XML exact Fraction RC budget diagnostic for native repair."""
import json
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
from buffered_rc_node_classes import read
from native_route_ledger_import_compact import physical_paths
R=Path(__file__).resolve().parents[1];D=R/'experiments/native_cold_branch_control_v8_2026-10-08'
case=next(c for c in json.loads((R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json').read_text())['cases'] if c['width']==32 and c['index']==2)
target=json.loads(Path(case['target']).read_text());graph=Path(target['inputs']['graph']['path']);route=D/'cold/output.route';budget=Path(case['budget']);b=json.loads(budget.read_text())
proof=D/'physical_endpoint_verification.json';p=json.loads(proof.read_text());assert p['all_target_connections_physical_endpoint_pass'] and all(sha(f)==h for f,h in p['bindings'].items())
bindings={**p['bindings'],str(proof):sha(proof),str(budget):sha(budget),str(Path(__file__)):sha(Path(__file__)),str(R/'tools/buffered_rc_node_classes.py'):sha(R/'tools/buffered_rc_node_classes.py')}
ids,classes,switches,digest=read(graph);assert digest==target['graph_sha256']
paths={}
for name,branches in physical_paths(route).items():
 for path in branches:
  key=(name,path[0][0],path[-1][0]);assert key not in paths;paths[key]=path
rows=[];violations=[]
for q in target['connections']:
 path=paths[target['net_names'][str(q['net_id'])],q['source'],q['sink']];r,c=classes[ids[q['source']]];delay=r*c/2
 for dst,switch in path[1:]:
  r,c=classes[ids[dst]];sr,td=switches[switch];delay+=(sr+r/2)*c+td
 limit=Fraction(b['budgets_ns'].get(str(q['connection_id']),b['default_budget_ns']))
 row=dict(connection_id=q['connection_id'],net_id=q['net_id'],delay_seconds=str(delay),budget_ns=str(limit),budget_pass=delay*10**9<=limit)
 rows.append(row)
 if not row['budget_pass']:violations.append(row)
assert len(rows)==len(paths)==1929 and all(sha(f)==h for f,h in bindings.items())
(D/'target_budget_verification.json').write_text(json.dumps(dict(bindings=bindings,complete_target_connections=1929,all_target_budgets_pass=not violations,violations=violations,rows=rows,scope='Exact supported buffered zero-internal-C additive XML RC model, not native STA equivalence or infeasibility of failed queries.'),indent=2)+'\n')
print('complete',len(rows),'budget violations',len(violations))
