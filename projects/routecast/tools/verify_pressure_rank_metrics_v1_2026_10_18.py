"""Histogram backend versus original full sort and exhaustive small tie sets."""
import json,random,itertools,hashlib
from pathlib import Path
from pressure_rank_metrics_v1 import top,metric
from prediction_metrics import compare
R=Path(__file__).resolve().parents[1];out=R/'experiments/pressure_rank_metrics_core_v1_2026-10-18';out.mkdir();rng=random.Random(20261018)
for trial in range(200):
 n=rng.randrange(1,65);p=[rng.randrange(7)/3 for _ in range(n)];t=[rng.randrange(6)/4 for _ in range(n)];k=rng.randrange(1,n+3)
 actual=metric(p,t,top(p,k),top(t,k));expected=compare(dict(enumerate(p)),dict(enumerate(t)),k)
 for name,value in expected.items():
  if name=='mae':continue
  if name=='spearman' and value is not None:assert abs(value-actual[name])<1e-12
  else:assert actual[name]==value
 if n<=8:
  for fixed,variable,values,key in [(top(p,k)['selected'],top(t,k),t,'fixed_prediction_truth_tie_hit_interval'),(top(t,k)['selected'],top(p,k),p,'fixed_truth_prediction_tie_hit_interval')]:
   above={i for i,v in enumerate(values) if v>variable['boundary']};equal={i for i,v in enumerate(values) if v==variable['boundary']}
   hits=[len(fixed&(above|set(selection))) for selection in itertools.combinations(equal,variable['k']-len(above))]
   assert actual[key]==[min(hits),max(hits)]
for values in [[],[float('nan')],[-1.0]]:
 try:top(values,1)
 except ValueError:pass
 else:raise AssertionError('invalid vector admitted')
paths=[Path(__file__),R/'tools/pressure_rank_metrics_v1.py',R/'tools/prediction_metrics.py']
with (out/'verification.json').open('x') as f:json.dump(dict(status='pass',random_vectors=200,exhaustive_small_tie_intervals=True,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}),f,indent=2)
print('PRESSURE METRIC CORE200 ORIGINAL-SORT AND TIE ORACLES PASS',flush=True)
