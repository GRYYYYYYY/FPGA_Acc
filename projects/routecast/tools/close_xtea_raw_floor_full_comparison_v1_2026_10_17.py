"""Close all metric outcomes without selecting a winner or changing defaults."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/xtea_raw_floor_full_comparison_v1_2026-10-17'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
p=D/'verification.json';d=json.loads(p.read_text());assert d['metric_vectors_independently_recomputed']==8 and not d['heldout_family']
assert all(sha(k)==h for k,h in d['bindings'].items())
m=d['metrics'];assert d['initial_ledgers_equal'] is False
rows=[]
for domain in ['concrete','spatial']:
 a=m['control1_sketch'][domain];b=m['proxy1_sketch'][domain]
 for metric in ['spearman','precision_at_k','recall_at_k','mae']:
  x,y=a[metric],b[metric]
  direction='undefined' if x is None or y is None else ('equal' if x==y else ('improved' if (y<x if metric=='mae' else y>x) else 'regressed'))
  rows.append(dict(domain=domain,metric=metric,control=x,proxy=y,outcome=direction))
result=dict(bindings={str(Path(__file__).resolve()):sha(__file__),str(p):sha(p),str(D/'protocol.json'):sha(D/'protocol.json')},all8_metric_sets_complete=True,initial_ledgers_equal=False,full_channel_universe=d['complete_channel_universe'],full_spatial_universe=d['complete_spatial_universe'],outcomes=rows,decision='Keep raw-floor engine as a development-only candidate: full initial floors/budgets are preserved, but changed equal-cost paths affect trajectory and all regressions remain material. No default promotion.',known_native_label_limit='Frozen labels exactly match canonical-audited cold route under ignored-pin semantic gate; original zero-counter gate remains false. No new candidate native run or QoR result.',scope='Same exposed XTEA labels and unchanged archived numeric tie policy. Not heldout, pooled cross-design aggregate, isolated path-recovery causality, native timing feasibility, complete workflow gain or hardware evidence.')
with (D/'research_decision_v1.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k!='bindings'},indent=2))
