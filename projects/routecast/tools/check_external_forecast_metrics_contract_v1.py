"""Hand-computed cases for exact bins, ties, zero entries and primary gate."""
import copy,json,hashlib
from fractions import Fraction
from pathlib import Path
from external_forecast_metrics_v1 import vectors,metrics,gate
R=Path(__file__).resolve().parents[1]
bin0=[0,1,1,'CHANX',0];bin1=[0,2,1,'CHANX',0]
resources=[dict(id=0,capacity=2,bins=[bin0,bin1]),dict(id=1,capacity=1,bins=[bin0]),dict(id=2,capacity=1,bins=[bin1]),dict(id=3,capacity=1,bins=[bin1])]
bins=[dict(key=bin0,capacity=3),dict(key=bin1,capacity=4)]
t=vectors(resources,bins,{0:2,1:1},5,truth=True)
assert t['resource']=={0:Fraction(1),1:Fraction(1),2:Fraction(0),3:Fraction(0)}
assert t['spatial']=={tuple(bin0):Fraction(1),tuple(bin1):Fraction(1,2)}
perfect=metrics(t,t,1,1);assert perfect['resource']['prediction_top_k']==[0] and perfect['resource']['top_k_hits']==1
assert not gate(perfect,perfect)['pass_primary_gate'] # strict improvement required
w=vectors(resources,bins,{2:1,3:1},5);wrong=metrics(w,t,1,1)
assert gate(perfect,wrong)['pass_primary_gate'] and not gate(wrong,perfect)['pass_primary_gate']
z=vectors(resources,bins,{},5);zero=metrics(z,t,1,1)
assert zero['resource']['universe_size']==4 and zero['resource']['spearman'] is None
assert not gate(perfect,zero)['pass_primary_gate'] # undefined control cannot pass
# Capacity normalization precedes deterministic topK: node1 beats node0.
a=vectors(resources,bins,{0:1,1:1},5);assert metrics(a,t,1,1)['resource']['prediction_top_k']==[1]
negative=[]
for name,ledger,truth in [('bool',{0:True},False),('negative',{0:-1},False),('out_of_graph',{5:1},False),('native_overflow',{0:3},True)]:
 try:vectors(resources,bins,ledger,5,truth=truth)
 except ValueError:negative.append(name)
 else:raise AssertionError(name)
# Prediction overuse remains observable rather than rejected as illegal routing.
assert vectors(resources,bins,{0:3},5)['resource'][0]==Fraction(3,2)
out=R/'experiments/prospective_external_family_forecast_metrics_contract_v1_2026-10-19';out.mkdir(exist_ok=False)
paths=[Path(__file__).resolve(),R/'tools/external_forecast_metrics_v1.py',R/'tools/prediction_metrics.py']
(out/'verification.json').write_text(json.dumps(dict(status='EXACT_CAPACITY_BIN_TIE_ZERO_AND_FOUR_METRIC_GATE_FIXTURES_PASS',bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},negative_contracts=negative,scope='Core metric/gate arithmetic only. No actual forecast or native label read; admission-aware case evaluator remains required.'),indent=2)+'\n')
print('FORECAST_METRIC_GATE_CONTRACT_PASS')
