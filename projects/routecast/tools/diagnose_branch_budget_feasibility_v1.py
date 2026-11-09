"""Classify exact per-connection budgets against certified relaxed floors."""
import json
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];F=R/'experiments/branch_budget_target_rr_floors_w32_m2_2026-10-08'
r=json.loads((F/'receipt.json').read_text());v=json.loads((F/'verification.json').read_text());assert sha(F/'receipt.json')==v['receipt_sha256'] and v['connections']==1929
p=json.loads((F/'protocol.json').read_text());assert sha(F/'protocol.json')==r['protocol_sha256'] and all(sha(f)==h for f,h in p['inputs'].items())
case=next(c for c in json.loads((R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json').read_text())['cases'] if c['width']==32 and c['index']==2)
budget=Path(case['budget']);b=json.loads(budget.read_text())
B=R/'experiments/branch_partial_budget_regressions_v1_2026-10-08/diagnosis.json';d=json.loads(B.read_text());assert all(sha(f)==h for f,h in d['bindings'].items())
bindings={**d['bindings'],**p['inputs'],str(B):sha(B),str(budget):sha(budget),str(Path(__file__)):sha(Path(__file__))}
for f in (F/'receipt.json',F/'protocol.json',F/'verification.json'):bindings[str(f)]=sha(f)
for c in r['certificates']:assert sha(c['path'])==c['sha256'];bindings[c['path']]=c['sha256']
rows=[];infeasible=[];byid={}
for x in r['rows']:
 q=x['query'];cid=q['connection_id'];floor=Fraction(x['minimum_integer'],r['scale']);limit=Fraction(b['budgets_ns'].get(str(cid),b['default_budget_ns']))
 y=dict(connection_id=cid,minimum_seconds=str(floor),budget_ns=str(limit),relaxed_budget_feasible=floor*10**9<=limit)
 rows.append(y);byid[cid]=y
 if not y['relaxed_budget_feasible']:infeasible.append(y)
D=R/'experiments/branch_budget_feasibility_v1_2026-10-08';D.mkdir(exist_ok=False)
assert len(rows)==1929 and all(sha(f)==h for f,h in bindings.items())
report=dict(bindings=bindings,connections=1929,relaxed_infeasible_budgets=infeasible,native_failure_classification=[dict(**x,certified_floor=byid[x['connection_id']]) for x in d['rows']],rows=rows,scope='Certified exact additive buffered RC positive-capacity independent path floor; infeasibility only in this model. Feasible individual floors do not imply joint capacity/shared-tree/native timing feasibility; budget not relaxed.')
(D/'diagnosis.json').write_text(json.dumps(report,indent=2)+'\n');print('certified relaxed budget infeasible',len(infeasible));print('native failure floors',[(x['connection_id'],byid[x['connection_id']]['relaxed_budget_feasible']) for x in d['rows']])
