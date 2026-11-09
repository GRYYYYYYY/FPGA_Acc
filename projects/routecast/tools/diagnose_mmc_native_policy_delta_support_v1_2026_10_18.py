"""Retrospective realized-update support and irreducible outside-support MAE."""
import json,sys,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
D=R/'experiments/mmc_native_policy_label_sensitivity_v3_2026-10-18';bindings=closure([Path(__file__)]);rows=[]
for case in ['case_01','case_02','case_03']:
 vp=(D/case/'verification.json').resolve();v=json.loads(vp.read_text());assert v['status']=='pass';vec=(D/case/'vectors.json').resolve();assert sha(vec)==v['bindings'][str(vec)];rp=(D/case/'comparison.json').resolve();assert sha(rp)==v['bindings'][str(rp)];r=json.loads(rp.read_text());data=json.loads(vec.read_text())
 for label in r['metrics']:
  for scope,items in [('concrete',data['channels']),('spatial',data['bins'])]:
   n=len(items);drift={i for i,x in enumerate(items) if x['labels'][label]!=x['predictions']['previous_native']};assert drift
   for mode in ['raw_min_off','raw_min_on','native_retained_off','native_retained_on','union_of_all4_realized_updates']:
    names=[mode] if mode!='union_of_all4_realized_updates' else ['raw_min_off','raw_min_on','native_retained_off','native_retained_on'];support={i for i,x in enumerate(items) if any(x['predictions'][m]!=x['predictions']['previous_native'] for m in names)};outside=drift-support
    floor=math.fsum(abs(items[i]['labels'][label]-items[i]['predictions']['previous_native'])/items[i]['capacity'] for i in outside)/n
    if len(names)==1:
     actual=math.fsum(abs(x['labels'][label]-x['predictions'][mode])/x['capacity'] for x in items)/n;assert math.isclose(actual,r['metrics'][label][mode][scope]['mae'],rel_tol=1e-12,abs_tol=1e-12) and floor<=actual+1e-12
    else:actual=None
    rows.append(dict(case=case,label=label,scope=scope,method=mode,universe=n,realized_update_support=len(support),true_label_drift_resources=len(drift),drift_outside_realized_support=len(outside),outside_fraction=len(outside)/len(drift),fixed_outside_support_MAE_floor=floor,actual_MAE=actual,outside_error_fraction=floor/actual if actual else None))
 for p in [vp,rp,vec]:bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items())
with (D/'realized_delta_support_diagnostic_v1.json').open('x') as f:json.dump(dict(bindings=bindings,rows=rows,scope='Retrospective decomposition of both native policy labels and unchanged five forecasts on all3exposed placements. Original cold-label and utility gates unchanged. Both label supports mandatory, no choosing the easier target. Posthoc decomposition of already verified full vectors. MAE floor assumes values outside the realized update support stay equal to old footprint and permits arbitrary perfect corrections inside. It is not a bound on other candidate routes/policies or rank/topK metrics, and not independent unseen/causal evidence.'),f,indent=2)
print('SUPPORT DIAGNOSTIC',[(x['case'],x['label'],x['scope'],x['outside_fraction'],x['outside_error_fraction']) for x in rows if x['method']=='native_retained_on'],flush=True)
