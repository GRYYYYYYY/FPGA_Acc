"""Retrospective proxy ordering audit; not a new prediction experiment."""
import json
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path
from pre_route_endpoints import sha
ROOT = Path(__file__).resolve().parents[1]
prior = ROOT/'experiments/mux_cold_actual_timing_model_2026-10-07'
rp, vp = prior/'receipt.json', prior/'verification.json'
r = json.loads(rp.read_text())
v = json.loads(vp.read_text())
assert v['receipt_sha256'] == sha(rp)
assert all(sha(p) == h for p,h in r['bindings'].items())
rows=[]
bindings={str(rp):sha(rp),str(vp):sha(vp),**r['bindings']}
for row in r['rows']:
    w,i=row['width'],row['index']
    p=ROOT/f'experiments/mux_full_cohort_cold_lifecycle_2026-10-06/mux_w{w}_m{i}_0/accepted_state.json'
    s=json.loads(p.read_text())
    delays=[F(q['answer']['delay']*10**9,s['scale']) for q in s['records']]
    assert delays and all(d>=0 for d in delays)
    rows.append(dict(width=w,index=i,max_connection_ns=str(max(delays)),dag_cpd_ns=row['actual_model_cpd_ns'],native_cpd_ns=row['accepted_native_cpd_ns']))
def sign(x): return (x>0)-(x<0)
pairs=[]
for a,b in combinations(rows,2):
    if a['width']!=b['width']: continue
    orders={k:sign(F(a[k])-F(b[k])) for k in ('max_connection_ns','dag_cpd_ns','native_cpd_ns')}
    pairs.append(dict(width=a['width'],indices=[a['index'],b['index']],orders=orders,proxy_native_disagrees=orders['max_connection_ns']!=orders['native_cpd_ns'],dag_native_disagrees=orders['dag_cpd_ns']!=orders['native_cpd_ns']))
out=ROOT/'experiments/max_connection_timing_order_2026-10-07'
out.mkdir(exist_ok=True)
result=dict(source_sha256=sha(Path(__file__)),bindings=bindings,rows=rows,pairs=pairs,proxy_native_order_disagreements=sum(p['proxy_native_disagrees'] for p in pairs),dag_native_order_disagreements=sum(p['dag_native_disagrees'] for p in pairs),scope='Retrospective 12 accepted MUX cold snapshots, within-width comparisons including ties. Native values rounded. Exact DAG arithmetic is not exact native STA; old local offsets and per-connection expansion RC remain assumptions. No new native execution, prospective selection, heldout guarantee or net gain.')
(out/'diagnosis.json').write_text(json.dumps(result,indent=2)+'\n')
print({k:result[k] for k in ('proxy_native_order_disagreements','dag_native_order_disagreements')})
print('within-width pairs',len(pairs))
