"""Fixed physical threshold; all rounds, no threshold fitting or round selection."""
import json,sys
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
D=R/'experiments/sha1_cold_iteration_routes_v1_2026-10-10';sp=D/'transient_label_summary_v2.json';s=json.loads(sp.read_text());assert s['snapshot_physical_label_audit_pass']
bindings={**s['bindings'],str(sp):sha(sp),**closure([Path(__file__)])};assert all(sha(k)==h for k,h in bindings.items())
vp=R/'experiments/sha1_frozen_hotspots_v2_2026-10-10/sha1/comparison_vectors.json';assert sha(vp)==bindings[str(vp)];cs=json.loads(vp.read_text())['channels'];universe={x['node'] for x in cs};assert len(universe)==len(cs)==28188
methods=['rc_initial','round0_shared','final_shared','final_independent'];pred={m:{c['node'] for c in cs if c['predictions'][m]>c['capacity']} for m in methods};rows=[]
for row in s['rows']:
 i=row['iteration'];ap=D/'snapshot_audits_v2'/f'iteration_{i:03d}.json';assert sha(ap)==bindings[str(ap)];a=json.loads(ap.read_text());truth={c['node'] for c in cs if a['node_occupancy'].get(str(c['node']),0)>c['capacity']};assert len(truth)==row['overused_channel_nodes'];metrics={}
 for m in methods:
  p=pred[m];tp=len(p&truth);fp=len(p-truth);fn=len(truth-p);tn=len(universe-(p|truth));assert tp+fp+fn+tn==len(universe)
  # Separate scalar booleans provide an independent complete confusion-table reconstruction.
  counts=Counter((c['predictions'][m]>c['capacity'],a['node_occupancy'].get(str(c['node']),0)>c['capacity']) for c in cs)
  assert [tp,fp,fn,tn]==[counts[True,True],counts[True,False],counts[False,True],counts[False,False]]
  metrics[m]=dict(tp=tp,fp=fp,fn=fn,tn=tn,predicted_positive=len(p),truth_positive=len(truth),precision=None if not p else tp/len(p),recall=None if not truth else tp/len(truth),f1=None if 2*tp+fp+fn==0 else 2*tp/(2*tp+fp+fn),false_positive_rate=None if not fp+tn else fp/(fp+tn))
 rows.append(dict(iteration=i,metrics=metrics))
assert [r['iteration'] for r in rows]==list(range(1,19));assert all(sha(k)==h for k,h in bindings.items())
(D/'transient_overflow_classification_v1.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,threshold='original per-node predicted/observed occupancy strictly greater than capacity',independent_confusion_tables_checked=72,scope='Exploratory same-design all-round fixed frozen prediction versus transient CHAN overflow classification. Undefined denominators explicitly null. Last legal round has no positive truth. No threshold tuning, heldout/failure prediction, causal time or hardware evidence.'),indent=2)+'\n')
print('PASS all72 overflow confusion tables')
for row in [rows[0],rows[-1]]:print(json.dumps(row))
