"""Account every surviving path against the full-fanin allocated budget."""
import json
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'experiments/mux_allfanin_priority32_2026-10-06'
alloc=ROOT/'experiments/mux_allfanin_budgets_2026-10-06'
r=json.loads((out/'receipt.json').read_text())
rows=[]
for row in r['rows']:
    w,i=row['width'],row['index']
    if row['status']=='ALLOCATION_NOT_SUBMITTED':
        rows.append(dict(width=w,index=i,status=row['status']));continue
    af=alloc/f'w{w}_m{i}.json';pf=out/f'w{w}_m{i}/prediction.json'
    a=json.loads(af.read_text());p=json.loads(pf.read_text());assert sha(pf)==row['prediction_sha256']
    violations=[]
    for rec in p['records']:
        cid=str(rec['connection_id']);delay=Fraction(rec['answer']['delay']*10**9,p['scale'])
        limit=Fraction(a['budgets_ns'][cid])
        if delay>limit:violations.append(dict(connection_id=int(cid),delay_ns=str(delay),budget_ns=str(limit)))
    rows.append(dict(width=w,index=i,status=row['status'],paths_checked=len(p['records']),budget_violations=violations,allocation_sha256=sha(af),prediction_sha256=sha(pf),complete=False))
(out/'actual_budget_accounting.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),auditor_sha256=sha(Path(__file__)),rows=rows,scope='Exact rational accounting of all surviving records, including retained paths. Partial records do not establish a complete timing vector or native STA result.'),indent=2)+'\n')
print([(x['width'],x['index'],len(x.get('budget_violations',[]))) for x in rows])
