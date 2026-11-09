"""Compare fully audited development prediction metrics under identical cold labels."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
folders=[R/'experiments/mmc_actual_old_linear_fallback_hotspots_v5_2026-10-09/mmc',R/'experiments/mmc_limited_hotspots_v7_2026-10-10/mmc']
bindings=closure([Path(__file__)]);reports=[];vectors=[]
for d in folders:
 for name in ['comparison.json','metric_verification.json','truth_tie_sensitivity.json']:
  p=d/name;r=json.loads(p.read_text());assert all(sha(k)==h for k,h in r['bindings'].items());bindings[str(p)]=sha(p)
  if name=='comparison.json':reports.append(r)
  if name=='metric_verification.json':assert r['histogram_ranks_topk_mae_and_full_vector_scope_pass'] and r['metric_vectors_recomputed']==9
 p=d/'comparison_vectors.json';vectors.append(json.loads(p.read_text()));bindings[str(p)]=sha(p)
old,new=reports;assert old['heldout_family']==new['heldout_family']==False and old['required']==new['required']==115572
for domain,key in [('concrete','channels'),('spatial','bins')]:
 a,b=[v[key] for v in vectors];assert len(a)==len(b)
 for x,y in zip(a,b):
  assert {k:v for k,v in x.items() if k!='predictions'}=={k:v for k,v in y.items() if k!='predictions'}
  assert x['predictions']['rc_initial']==y['predictions']['rc_initial']
rows=[]
for method in old['metrics']:
 for domain in ['concrete','spatial']:
  a,b=old['metrics'][method][domain],new['metrics'][method][domain]
  if a is None:assert b is None;continue
  assert a['universe_size']==b['universe_size'] and a['k']==b['k'] and a['top_k_tie_rule']==b['top_k_tie_rule']
  rows.append(dict(method=method,domain=domain,baseline=a,candidate=b,deltas={key:b[key]-a[key] if b[key] is not None and a[key] is not None else None for key in ['spearman','mae','precision_at_k','recall_at_k']}))
assert all(sha(k)==h for k,h in bindings.items())
D=R/'experiments/mmc_limited_vs_span_metrics_v2_2026-10-10';D.mkdir(exist_ok=True)
(D/'comparison.json').write_text(json.dumps(dict(bindings=bindings,matched_complete_metadata_cold_labels_geometry_and_initial_predictions=True,rows=rows,scope='Post-hoc same-design development ablation under full semantic and independent numerical audits; same complete resource/spatial universe/k/tie rule. No parameter tuning after candidate results. No strict-heldout, native QoR, routability failures or complete runtime gain evidence.'),indent=2)+'\n')
print(json.dumps([dict(method=x['method'],domain=x['domain'],deltas=x['deltas']) for x in rows],indent=2))
