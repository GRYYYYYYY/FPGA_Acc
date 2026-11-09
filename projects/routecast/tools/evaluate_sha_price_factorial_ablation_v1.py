"""All8 ablation configurations, full discrete and spatial vectors, independent histogram metric oracle."""
import ast,json,sys,math,xml.etree.ElementTree as E
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from prediction_metrics import compare
R=Path(__file__).resolve().parents[1];D=R/'experiments/sha_price_factorial_ablation_v2_2026-10-10';p=D/'independent_verification.json';proof=json.loads(p.read_text());assert proof['all8_full_query_models_and_complete_audits_pass'] and all(sha(q)==h for q,h in proof['bindings'].items());bindings={str(p):sha(p),str(Path(__file__)):sha(Path(__file__)),str(R/'tools/prediction_metrics.py'):sha(R/'tools/prediction_metrics.py')}
oracle=R/'tools/verify_aes_native_demand_span_ablation_hotspots_v1.py';fn=next(n for n in ast.parse(oracle.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='audit_metric');checked=0;exec(compile(ast.Module(body=[fn],type_ignores=[]),str(oracle),'exec'));bindings[str(oracle)]=sha(oracle)
plan=json.loads((D/'protocol.json').read_text())['plans'];rows=[]
for case,root in [('original','sha1_frozen_hotspots_v2_2026-10-10'),('second_swap','sha_second_swap_hotspots_v1_2026-10-10')]:
 B=R/'experiments'/root/'sha1';vp=B/'comparison_vectors.json';mp=B/'metric_verification.json';v=json.loads(mp.read_text());assert v['histogram_ranks_topk_mae_and_full_vector_scope_pass'] and all(sha(q)==h for q,h in v['bindings'].items());bindings.update({str(q):sha(q) for q in [vp,mp]});vectors=json.loads(vp.read_text());truth={x['node']:x['native']/x['capacity'] for x in vectors['channels']};caps={x['node']:x['capacity'] for x in vectors['channels']};bins={tuple(x['key']):x for x in vectors['bins']};epfile=Path(next(x['endpoint'] for x in plan if x['case']==case));ep=json.loads(epfile.read_text());graph=Path(ep['inputs']['graph']['path']);assert sha(graph)==ep['graph_sha256'];bindings[str(graph)]=sha(graph);incidence={};capacity=Counter();stack=[]
 for event,x in E.iterparse(graph,events=['start','end']):
  if event=='start':stack.append(x);continue
  if x.tag=='node' and x.get('type') in ['CHANX','CHANY'] and int(x.get('capacity'))>0:
   n=int(x.get('id'));assert n in caps and caps[n]==int(x.get('capacity'));loc=x.find('loc').attrib;seg=x.find('segment');sid=int(seg.get('segment_id')) if seg is not None else -1
   keys=[(int(loc.get('layer','0')),xx,yy,x.get('type'),sid) for xx in range(int(loc['xlow']),int(loc['xhigh'])+1) for yy in range(int(loc['ylow']),int(loc['yhigh'])+1)];incidence[n]=keys
   for k in keys:capacity[k]+=caps[n]
  if x.tag in ['node','edge']:
   if len(stack)>1:stack[-2].remove(x)
   x.clear()
  stack.pop()
 assert set(incidence)==set(truth) and set(capacity)==set(bins) and all(capacity[k]==bins[k]['capacity'] for k in bins)
 native=Counter()
 for n,keys in incidence.items():
  for k in keys:native[k]+=int(truth[n]*caps[n])
 assert all(native[k]==bins[k]['native'] for k in bins);sptruth={k:native[k]/capacity[k] for k in bins}
 geometry={k:bins[k]['geometry'] for k in bins};geo_metric=compare(geometry,sptruth,20);audit_metric(geometry,sptruth,geo_metric,20)
 for mode in ['both','no_span','no_overuse','neither']:
  W=D/case/mode/'model';metrics={}
  for method,filename,field in [('initial','initial.json','ledger'),('round0','round0.json','ledger'),('final_shared','sketch.json','ledger'),('final_independent','sketch.json','independent_connection_ledger')]:
   q=W/filename;state=json.loads(q.read_text());bindings[str(q)]=sha(q);ledger=state[field];pred={n:ledger.get(str(n),0)/caps[n] for n in truth};sp=Counter()
   for n,keys in incidence.items():
    for k in keys:sp[k]+=ledger.get(str(n),0)
   sppred={k:sp[k]/capacity[k] for k in bins};a=compare(pred,truth,1409);b=compare(sppred,sptruth,20);audit_metric(pred,truth,a,1409);audit_metric(sppred,sptruth,b,20);metrics[method]=dict(concrete=a,spatial=b,absolute_resource_count_error=sum(abs(ledger.get(str(n),0)-int(truth[n]*caps[n])) for n in truth),overflow_units=sum(max(0,ledger.get(str(n),0)-caps[n]) for n in truth))
  row=dict(case=case,mode=mode,metrics=metrics,geometry_spatial=geo_metric);rows.append(row);print(case,mode,{m:dict(error=x['absolute_resource_count_error'],resource_rho=x['concrete']['spearman'],spatial_rho=x['spatial']['spearman']) for m,x in metrics.items()},flush=True)
assert checked==66 and len(rows)==8 and all(sha(q)==h for q,h in bindings.items());(D/'comparison.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,independent_histogram_metric_checks=checked,scope='All8 exposeddevelopment factor settings/all28188CHANs/all1680bins, complete vectors and fixedtopk with independent metric oracle. No selected best policy or parameter tuning, strictheldout/native failure/timing claim.'),indent=2)+'\n')
