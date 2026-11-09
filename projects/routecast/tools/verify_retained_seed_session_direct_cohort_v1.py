"""Authenticate full12 direct-import seeds against original frozen CSR seed cohort."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/retained_seed_session_direct_cohort_v1_2026-10-08';B=R/'experiments/retained_seed_session_cohort_v3_2026-10-08'
r=json.loads((D/'receipt.json').read_text());b=json.loads((B/'receipt.json').read_text());bindings={}
for doc in (r,b):
 assert all(sha(f)==h for f,h in doc['bindings'].items());bindings.update(doc['bindings'])
assert len(r['rows'])==len(b['rows'])==12 and r['cache_stats']['builds']==3
rows=[]
for x,y in zip(r['rows'],b['rows']):
 assert (x['width'],x['index'],x['retained'],x['released'],x['retained_nets'])==(y['width'],y['index'],y['retained'],y['released'],y['retained_nets'])
 assert x['route_sha256']==y['route_sha256'] and Path(x['route']).read_bytes()==Path(y['route']).read_bytes()
 xf=Path(x['route']).with_name('forest.json');yf=Path(y['route']).with_name('forest.json')
 assert json.loads(xf.read_text())==json.loads(yf.read_text())
 bindings[str(yf)]=sha(yf)
 rows.append(dict(width=x['width'],index=x['index'],retained=x['retained'],released=x['released'],seed_bytes_forest_equal=True))
for p in (D/'receipt.json',B/'receipt.json',Path(__file__)):
 bindings[str(p)]=sha(p)
report=dict(bindings=bindings,rows=rows,all12_original_budget_forests_and_seed_bytes_equal=True,observed_direct_seed_component_seconds=r['cohort_component_seconds'],reference_seed_component_seconds=b['cohort_component_seconds'],scope='Full12 original-budget retention, native trace pin/header serialization and seed bytes identical to frozen CSR-based v3. Independent baseline includes prior pin/forest proofs. Single historical versus current component timings; no new native execution, shared-inventory downstream audit or end-to-end gain. No route epoch advancement.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k not in ('bindings','rows')})
