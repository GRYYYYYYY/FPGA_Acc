"""Independently recompute all fixed-cohort admission decisions from authenticated proofs."""
import json
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/branch_budget_admission_census_v1_2026-10-08';rp=D/'receipt.json';p=json.loads((D/'protocol.json').read_text());r=json.loads(rp.read_text());assert sha(D/'protocol.json')==r['protocol_sha256'] and all(sha(f)==h for f,h in p['bindings'].items())
expected={(w,i) for w in (8,16,32) for i in range(4)};assert {(c['width'],c['index']) for c in p['cases']}==expected and {(c['width'],c['index']) for c in r['rows']}==expected and len(r['rows'])==r['complete_cases']==12
bindings={**p['bindings'],str(rp):sha(rp),str(Path(__file__)):sha(Path(__file__))};cases={(c['width'],c['index']):c for c in p['cases']};rows=[]
for row in r['rows']:
 c=cases[row['width'],row['index']];ap=Path(row['admission_path']);assert sha(ap)==row['admission_sha256'];a=json.loads(ap.read_text());assert all(sha(f)==h for f,h in a['bindings'].items());bindings.update(a['bindings']);bindings[str(ap)]=sha(ap)
 ep=json.loads(Path(c['target']).read_text());budget=json.loads(Path(c['budget']).read_text());queries={q['connection_id']:q for q in ep['connections']}
 proofs=[Path(f) for f in a['bindings'] if Path(f).name=='receipt.json'];assert len(proofs)==1;fp=proofs[0];floor=json.loads(fp.read_text());vp=fp.with_name('verification.json');v=json.loads(vp.read_text());assert v['receipt_sha256']==sha(fp) and v['connections']==len(queries)
 assert floor['graph_sha256']==ep['graph_sha256'] and len(floor['rows'])==len(queries) and {x['query']['connection_id'] for x in floor['rows']}==set(queries)
 recomputed=[]
 for x in floor['rows']:
  q=x['query'];assert q==queries[q['connection_id']] and x['status']=='FOUND';minimum=Fraction(x['minimum_integer'],floor['scale']);limit=Fraction(budget['budgets_ns'].get(str(q['connection_id']),budget['default_budget_ns']))
  recomputed.append(dict(connection_id=q['connection_id'],minimum_seconds=str(minimum),budget_ns=str(limit),relaxed_path_budget_feasible=minimum*10**9<=limit))
 assert a['rows']==recomputed;bad=[x for x in recomputed if not x['relaxed_path_budget_feasible']];assert a['blockers']==bad and a['admitted']==(not bad) and row['admitted']==a['admitted'] and row['blockers']==[x['connection_id'] for x in bad]
 before=json.loads(Path(c['old']).read_text());old={q['connection_id']:q for q in before['connections']}
 unchanged=[x['connection_id'] for x in bad if (old[x['connection_id']]['source'],old[x['connection_id']]['sink'])==(queries[x['connection_id']]['source'],queries[x['connection_id']]['sink'])]
 rows.append(dict(width=row['width'],index=row['index'],connections=len(queries),admitted=not bad,blockers=len(bad),endpoint_unchanged_blocker_ids=unchanged,endpoint_changed_blocker_ids=[x['connection_id'] for x in bad if x['connection_id'] not in unchanged]));bindings[c['old']]=sha(c['old'])
assert sum(x['admitted'] for x in rows)==r['admitted_cases'] and all(sha(f)==h for f,h in bindings.items())
report=dict(bindings=bindings,all_twelve_cases_independent_admission_pass=True,admitted_cases=r['admitted_cases'],rows=rows,scope='Admission decision and certificate authentication replay, complete fixed developer cohort; floors optimality established by bound independent inequality proofs, no performance/heldout or new budget policy.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('verified all12, admitted',r['admitted_cases']);print(rows)
