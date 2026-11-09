"""Evaluate sealed DEVELOPMENT timing decisions against published/native CPDs."""
import json
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'experiments/live_state_dag_screen_replay_2026-10-07'
rp=base/'receipt.json';r=json.loads(rp.read_text())
assert all(sha(p)==h for p,h in r['sources'].items())
assert all(sha(p)==h for x in r['rows'] for p,h in x['inputs'].items())
op=ROOT/'experiments/mux_old_full_timing_graph_2026-10-06/receipt.json'
ov=op.parent/'recurrence_verification.json'
old=json.loads(op.read_text());v=json.loads(ov.read_text());assert v['receipt_sha256']==sha(op)
for x in old['rows']:
 assert x['exit_code']==0 and x['mismatches']==x['fixups']==0
 assert all(sha(p)==h for p,h in x['files'].items())
published={x['width']:F(str(x['cpd_ns'])) for x in old['rows']}
cp=ROOT/'experiments/mux_cold_actual_timing_model_2026-10-07/receipt.json';cv=cp.parent/'verification.json'
c=json.loads(cp.read_text());assert json.loads(cv.read_text())['receipt_sha256']==sha(cp)
assert all(sha(p)==h for p,h in c['bindings'].items())
labels={(x['width'],x['index']):x for x in c['rows']}
rows=[]
for x in r['rows']:
 w,i=x['width'],x['index'];d=x['decision'];q=labels[w,i]
 assert F(d['candidate_model_cpd_ns'])==F(q['actual_model_cpd_ns'])
 native=F(q['accepted_native_cpd_ns']);gain=published[w]-native
 modelgain=F(d['published_model_cpd_ns'])-F(d['candidate_model_cpd_ns'])
 admitted=d['model_admitted'];nativepass=gain>=0
 rows.append(dict(width=w,index=i,model_admitted=admitted,native_timing_nonregression=nativepass,model_gain_ns=str(modelgain),native_gain_ns=str(gain),false_timing_admission=admitted and not nativepass,missed_native_timing_nonregression=not admitted and nativepass,model_gain_minus_native_gain_ns=str(modelgain-gain),exact_model_tie=modelgain==0,rounded_native_tie=gain==0))
result=dict(source_sha256=sha(Path(__file__)),bindings={str(p):sha(p) for p in (rp,op,ov,cp,cv)},rows=rows,false_timing_admissions=sum(x['false_timing_admission'] for x in rows),missed_native_timing_nonregressions=sum(x['missed_native_timing_nonregression'] for x in rows),maximum_absolute_gain_error_ns=str(max(abs(F(x['model_gain_minus_native_gain_ns'])) for x in rows)),scope='DEVELOPMENT retrospective sealed timing-only decisions, comparison against published old native state. Native CPDs rounded; ties accepted under existing rule, no rule tuning. Wire excluded, no joint-quality/heldout/netgain guarantee. Existing archived native proofs reused, no new native run.')
(base/'native_decision_evaluation.json').write_text(json.dumps(result,indent=2)+'\n')
print({k:result[k] for k in ('false_timing_admissions','missed_native_timing_nonregressions','maximum_absolute_gain_error_ns')})
print([(x['width'],x['index'],x['exact_model_tie'],x['rounded_native_tie']) for x in rows])
