"""All rounds, frozen ledgers, full CHAN universe; exploratory transient occupancy."""
import ast,json,sys,math
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from prediction_metrics import compare
D=R/'experiments/sha1_cold_iteration_routes_v1_2026-10-10';sp=D/'transient_label_summary_v2.json';s=json.loads(sp.read_text());assert s['snapshot_physical_label_audit_pass']
bindings={**s['bindings'],str(sp):sha(sp),**closure([Path(__file__)])};assert all(sha(k)==h for k,h in bindings.items())
vp=R/'experiments/sha1_frozen_hotspots_v2_2026-10-10/sha1/comparison_vectors.json';assert sha(vp)==bindings[str(vp)];channels=json.loads(vp.read_text())['channels'];assert len(channels)==s['positive_capacity_channel_universe']==28188
predictions={m:{c['node']:c['predictions'][m]/c['capacity'] for c in channels} for m in ['rc_initial','round0_shared','final_shared','final_independent']};k=max(1,len(channels)//20)
# Independent histogram-rank oracle, function body unchanged.
oracle=R/'tools/verify_aes_native_demand_span_ablation_hotspots_v1.py';bindings[str(oracle)]=sha(oracle);fn=next(n for n in ast.parse(oracle.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='audit_metric');checked=0
exec(compile(ast.Module(body=[fn],type_ignores=[]),str(oracle),'exec'))
rows=[]
for row in s['rows']:
 i=row['iteration'];ap=D/'snapshot_audits_v2'/f'iteration_{i:03d}.json';assert sha(ap)==bindings[str(ap)];a=json.loads(ap.read_text());truth={c['node']:a['node_occupancy'].get(str(c['node']),0)/c['capacity'] for c in channels};metrics={};ties={}
 for method,pred in predictions.items():
  m=compare(pred,truth,k);audit_metric(pred,truth,m,k);metrics[method]=m
  boundary=m['truth_k_boundary'];strict={n for n,v in truth.items() if v>boundary};tied={n for n,v in truth.items() if v==boundary};selected=set(sorted(pred,key=lambda n:(-pred[n],n))[:k]);need=k-len(strict);assert 0<need<=len(tied);fixed=len(selected&strict);possible=len(selected&tied)
  lo=(fixed+max(0,need-(len(tied)-possible)))/k;hi=(fixed+min(need,possible))/k;assert lo<=m['precision_at_k']<=hi;ties[method]=dict(truth_tie_precision_lower=lo,truth_tie_precision_upper=hi)
 rows.append(dict(iteration=i,metrics=metrics,truth_cutoff_tie_sensitivity=ties))
assert checked==72 and [r['iteration'] for r in rows]==list(range(1,19))
assert all(sha(k)==h for k,h in bindings.items())
out=D/'transient_resource_metrics_v1.json';out.write_text(json.dumps(dict(bindings=bindings,rows=rows,independent_histogram_metric_recomputations=checked,resource_k=k,scope='Exploratory all18 full positive CHAN normalized occupancy correlations and top5% (floor), fixed predicted ID order/all truth cutoff ties. Original models unchanged; no selected round, tuning, spatial metrics or binary excess-capacity classification in this artifact. Not prospective transient accuracy, heldout, failure or speedup proof.'),indent=2)+'\n')
print('PASS all18 resource metrics independently recomputed',checked)
for i in [0,-1]:print(rows[i]['iteration'],{m:dict(spearman=x['spearman'],precision=x['precision_at_k']) for m,x in rows[i]['metrics'].items()})
