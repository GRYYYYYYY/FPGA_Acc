"""Same earlier mechanism, exact predictions and updates under cached backend."""
import json
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_retained_joint_cached_reroute_2026-10-06';old=ROOT/'experiments/mux_retained_joint_reroute_2026-10-06';budgets=ROOT/'experiments/mux_retained_joint_budgets_2026-10-06'
def read(p):return json.loads(p.read_text())
p=read(out/'protocol.json');bp=read(old/'protocol.json');r=read(out/'receipt.json');br=read(old/'receipt.json')
assert p['cases']==bp['cases'] and p['allocations']==bp['allocations'] and len(r['rows'])==len(br['rows'])==12
assert r['protocol_sha256']==sha(out/'protocol.json') and br['protocol_sha256']==sha(old/'protocol.json')
assert p['parent_protocol_sha256']==bp['parent_protocol_sha256']==sha(budgets/'protocol.json')
assert all(sha(f)==h for f,h in p['sources'].items())
rows=[]
for c,a,b in zip(p['cases'],r['rows'],br['rows']):
 w,i=c['width'],c['index'];assert (w,i)==(a['width'],a['index'])==(b['width'],b['index']) and a['status']==b['status']
 assert all(sha(f)==h for f,h in c['inputs'].items())
 if a['status']=='ALLOCATION_NOT_SUBMITTED':assert a==b;rows.append(a);continue
 work=out/f'w{w}_m{i}';baseline=old/f'w{w}_m{i}'
 assert (work/'prediction.json').read_bytes()==(baseline/'prediction.json').read_bytes()
 assert (work/'update.json').read_bytes()==(baseline/'update.json').read_bytes()
 assert a['prediction_sha256']==b['prediction_sha256']==sha(work/'prediction.json')
 for key in ('completed','required','failure'):assert a[key]==b[key]
 rows.append(dict(**a,baseline_stage_seconds=b['stage_seconds'],update_sha256=sha(work/'update.json')))
(out/'verification.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),receipt_sha256=sha(out/'receipt.json'),baseline_receipt_sha256=sha(old/'receipt.json'),cohort_cost_sha256=sha(out/'cohort_cost.json'),rows=rows,scope='Full12 earlier retained-joint diagnostic allocation outcomes and all5 actual prediction/update files byte-identical under owned cached search; search binary intentionally differs. Same original historical budget vectors, no new oracle-free allocation/native acceptance/publication claim. Shared-per-width common-old-ledger alternative cases, not accepted sequential state. Setup/stage/serialization cost recorded, original budget preparation/native gate/audits excluded.'),indent=2)+'\n');print([(x['width'],x['index'],x['status']) for x in rows])
