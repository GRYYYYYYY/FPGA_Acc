"""Fixed geometry rule retrospective audit; never tune using quality labels."""
import json
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path
from pre_route_endpoints import sha
ROOT = Path(__file__).resolve().parents[1]
geometry = ROOT/'experiments/incremental_net_geometry_2026-10-07/verification.json'
joint = ROOT/'experiments/live_state_dag_screen_replay_2026-10-07/joint_decision_evaluation.json'
timing = joint.parent/'native_decision_evaluation.json'
old = ROOT/'experiments/mux_old_full_timing_graph_2026-10-06/receipt.json'
current = ROOT/'experiments/mux_full_cohort_cold_lifecycle_2026-10-06/receipt.json'
verification = current.parent/'verification.json'
g,j,t,o,c,v = [json.loads(p.read_text()) for p in (geometry,joint,timing,old,current,verification)]
assert v['receipt_sha256'] == sha(current)
bindings = {str(p):sha(p) for p in (geometry,joint,timing,old,current,verification,Path(__file__))}
for record in (g,j):
    for path, digest in record['bindings'].items():
        assert sha(path) == digest
        bindings[path] = digest
lookup = lambda rows: {(r['width'],r['index']):r for r in rows}
js,ts,cs=lookup(j['rows']),lookup(t['rows']),lookup(c['rows'])
published = {r['width']:F(str(r['cpd_ns'])) for r in o['rows']}
rows=[]
for x in g['cases']:
    key=x['width'],x['index']; q, label, native=js[key],ts[key],cs[key]
    assert native['complete'] and native['error'] is None
    nr=native['rounds'][0]['native']
    for path,digest in nr['files'].items():
        assert sha(path)==digest
        bindings[path]=digest
    cpd=F(str(nr['cpd_ns']))
    assert published[x['width']]-cpd==F(label['native_gain_ns'])
    log=next(Path(p) for p in nr['files'] if p.endswith('/run.log'))
    import re
    wire=int(re.findall(r'Total wirelength:\s*(\d+)',log.read_text())[-1])
    assert wire==q['candidate_wirelength']
    joint_ok=cpd<=published[x['width']] and wire<=q['published_wirelength']
    assert joint_ok==q['native_joint_nonregression']
    rows.append(dict(width=x['width'],index=x['index'],delta_hpwl=x['delta_hpwl'],geometry_selected=x['selected_strict_hpwl_rule'],native_cpd_ns=str(cpd),native_wirelength=wire,delta_native_wirelength=wire-q['published_wirelength'],native_gain_ns=label['native_gain_ns'],native_joint_nonregression=joint_ok,missed_joint_nonregression=joint_ok and not x['selected_strict_hpwl_rule']))
def sign(x): return (x>0)-(x<0)
pairs=[]
for a,b in combinations(rows,2):
    if a['width']!=b['width']:continue
    geometric=sign(a['delta_hpwl']-b['delta_hpwl'])
    wire=sign(a['native_wirelength']-b['native_wirelength'])
    delay=sign(F(a['native_cpd_ns'])-F(b['native_cpd_ns']))
    pairs.append(dict(width=a['width'],indices=[a['index'],b['index']],geometry_order=geometric,wire_order=wire,cpd_order=delay,wire_order_disagreement=geometric!=wire,cpd_order_disagreement=geometric!=delay))
assert len(rows)==12 and len(pairs)==18
assert all(sha(p)==h for p,h in bindings.items())
report=dict(bindings=bindings,rows=rows,pairs=pairs,missed_joint_nonregressions=sum(r['missed_joint_nonregression'] for r in rows),wire_order_disagreements=sum(p['wire_order_disagreement'] for p in pairs),cpd_order_disagreements=sum(p['cpd_order_disagreement'] for p in pairs),scope='Retrospective existing development family, fixed strict HPWL rule unchanged. Compare target cold-route quality to OLD published state, not incremental route candidate vs same-target cold. Native CPD rounded; tie disagreement retained. No new native execution, oracle-free quality guarantee, threshold tuning, prospective or net gain evidence.')
out=ROOT/'experiments/geometry_quality_order_2026-10-07';out.mkdir(exist_ok=False)
(out/'diagnosis.json').write_text(json.dumps(report,indent=2)+'\n')
print({k:report[k] for k in ('missed_joint_nonregressions','wire_order_disagreements','cpd_order_disagreements')})
print([(r['width'],r['index'],r['delta_hpwl'],r['delta_native_wirelength'],r['native_joint_nonregression']) for r in rows])
