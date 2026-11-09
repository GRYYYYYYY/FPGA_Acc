"""All rounds, frozen ledgers, full CHAN universe; exploratory transient occupancy."""
import ast,json,sys,math,xml.etree.ElementTree as E
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from prediction_metrics import compare
D=R/'experiments/sha1_cold_iteration_routes_v1_2026-10-10';sp=D/'transient_label_summary_v2.json';s=json.loads(sp.read_text());assert s['snapshot_physical_label_audit_pass']
bindings={**s['bindings'],str(sp):sha(sp),**closure([Path(__file__)])};assert all(sha(k)==h for k,h in bindings.items())
vp=R/'experiments/sha1_frozen_hotspots_v2_2026-10-10/sha1/comparison_vectors.json';assert sha(vp)==bindings[str(vp)];vectors=json.loads(vp.read_text());channels=vectors['channels'];bins=vectors['bins'];assert len(channels)==s['positive_capacity_channel_universe']==28188
# Reconstruct channel-to-bin incidence directly from original XML.
epf=R/'experiments/sha1_actual_old_linear_expat_workflow_v1_2026-10-10/cold/demand/sha1/endpoints.json';ep=json.loads(epf.read_text());graph=Path(ep['inputs']['graph']['path']);assert sha(graph)==ep['graph_sha256'];assert bindings[str(graph)]==sha(graph)
incidence={};capacities=Counter();stack=[]
for event,el in E.iterparse(graph,events=('start','end')):
 if event=='start':stack.append(el);continue
 if el.tag=='node' and el.get('type') in {'CHANX','CHANY'} and int(el.get('capacity'))>0:
  n=int(el.get('id'));cap=int(el.get('capacity'));loc=el.find('loc').attrib;segment=el.find('segment');seg=int(segment.get('segment_id')) if segment is not None else -1
  keys=[(int(loc.get('layer','0')),x,y,el.get('type'),seg) for x in range(int(loc['xlow']),int(loc['xhigh'])+1) for y in range(int(loc['ylow']),int(loc['yhigh'])+1)];assert n not in incidence;incidence[n]=keys
  for key in keys:capacities[key]+=cap
 if el.tag in {'node','edge'}:
  if len(stack)>1:stack[-2].remove(el)
  el.clear()
 stack.pop()
assert set(incidence)=={c['node'] for c in channels} and len(bins)==1680 and set(capacities)=={tuple(b['key']) for b in bins}
assert all(capacities[tuple(b['key'])]==b['capacity'] for b in bins)
methods=['rc_initial','round0_shared','final_shared','final_independent']
for method in methods:
 rebuilt=Counter()
 for c in channels:
  for key in incidence[c['node']]:rebuilt[key]+=c['predictions'][method]
 assert all(rebuilt[tuple(b['key'])]==b['predictions'][method] for b in bins)
predictions={m:{tuple(b['key']):b['predictions'][m]/b['capacity'] for b in bins} for m in methods}
predictions['geometry']={tuple(b['key']):b['geometry'] for b in bins};k=20
# Independent histogram-rank oracle, function body unchanged.
oracle=R/'tools/verify_aes_native_demand_span_ablation_hotspots_v1.py';bindings[str(oracle)]=sha(oracle);fn=next(n for n in ast.parse(oracle.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='audit_metric');checked=0
exec(compile(ast.Module(body=[fn],type_ignores=[]),str(oracle),'exec'))
rows=[]
for row in s['rows']:
 i=row['iteration'];ap=D/'snapshot_audits_v2'/f'iteration_{i:03d}.json';assert sha(ap)==bindings[str(ap)];a=json.loads(ap.read_text());demand=Counter()
 for n,keys in incidence.items():
  for key in keys:demand[key]+=a['node_occupancy'].get(str(n),0)
 truth={key:demand[key]/capacities[key] for key in capacities};metrics={};ties={}
 for method,pred in predictions.items():
  m=compare(pred,truth,k);audit_metric(pred,truth,m,k);metrics[method]=m
  boundary=m['truth_k_boundary'];strict={n for n,v in truth.items() if v>boundary};tied={n for n,v in truth.items() if v==boundary};selected=set(sorted(pred,key=lambda n:(-pred[n],n))[:k]);need=k-len(strict);assert 0<need<=len(tied);fixed=len(selected&strict);possible=len(selected&tied)
  lo=(fixed+max(0,need-(len(tied)-possible)))/k;hi=(fixed+min(need,possible))/k;assert lo<=m['precision_at_k']<=hi;ties[method]=dict(truth_tie_precision_lower=lo,truth_tie_precision_upper=hi)
 rows.append(dict(iteration=i,metrics=metrics,truth_cutoff_tie_sensitivity=ties))
assert checked==90 and [r['iteration'] for r in rows]==list(range(1,19))
assert all(sha(k)==h for k,h in bindings.items())
out=D/'transient_spatial_metrics_v1.json';out.write_text(json.dumps(dict(bindings=bindings,rows=rows,independent_histogram_metric_recomputations=checked,spatial_k=k,scope='Exploratory all18 full original CHAN bbox spatial normalized occupancy correlations and top20, fixed predicted ID order/all truth cutoff ties. Original models unchanged; no selected round, tuning, resource metrics or binary excess-capacity classification in this artifact. Not prospective transient accuracy, heldout, failure or speedup proof.'),indent=2)+'\n')
print('PASS all18 spatial metrics independently recomputed',checked)
for i in [0,-1]:print(rows[i]['iteration'],{m:dict(spearman=x['spearman'],precision=x['precision_at_k']) for m,x in rows[i]['metrics'].items()})
