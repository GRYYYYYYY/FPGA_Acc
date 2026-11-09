"""All18 audited iterations, all frozen factors/representations; exploratory transient occupancy and overuse."""
import ast,json,sys,math,xml.etree.ElementTree as E
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from prediction_metrics import compare
R=Path(__file__).resolve().parents[1];D=R/'experiments/sha_price_factorial_ablation_v2_2026-10-10';L=R/'experiments/sha1_cold_iteration_routes_v1_2026-10-10'
p=D/'independent_verification.json';proof=json.loads(p.read_text());assert proof['all8_full_query_models_and_complete_audits_pass'] and all(sha(q)==h for q,h in proof['bindings'].items());sp=L/'transient_label_summary_v2.json';s=json.loads(sp.read_text());assert s['snapshot_physical_label_audit_pass'] and all(sha(q)==h for q,h in s['bindings'].items());bindings={**s['bindings'],str(sp):sha(sp),str(p):sha(p),str(Path(__file__)):sha(Path(__file__)),str(R/'tools/prediction_metrics.py'):sha(R/'tools/prediction_metrics.py')}
epfile=R/'experiments/sha1_compact_json_complete_workflow_v1_2026-10-10/seed/demand/sha1/endpoints.json';ep=json.loads(epfile.read_text());graph=Path(ep['inputs']['graph']['path']);assert sha(graph)==ep['graph_sha256'];bindings[str(graph)]=sha(graph);caps={};incidence={};spcaps=Counter();stack=[]
for event,x in E.iterparse(graph,events=['start','end']):
 if event=='start':stack.append(x);continue
 if x.tag=='node' and x.get('type') in ['CHANX','CHANY'] and int(x.get('capacity'))>0:
  n=int(x.get('id'));cap=int(x.get('capacity'));assert cap==1;caps[n]=cap;loc=x.find('loc').attrib;seg=x.find('segment');sid=int(seg.get('segment_id')) if seg is not None else -1
  keys=[(int(loc.get('layer','0')),xx,yy,x.get('type'),sid) for xx in range(int(loc['xlow']),int(loc['xhigh'])+1) for yy in range(int(loc['ylow']),int(loc['yhigh'])+1)];incidence[n]=keys
  for k in keys:spcaps[k]+=cap
 if x.tag in ['node','edge']:
  if len(stack)>1:stack[-2].remove(x)
  x.clear()
 stack.pop()
assert len(caps)==28188 and len(spcaps)==1680
predictions={}
for mode in ['both','no_span','no_overuse','neither']:
 W=D/'original'/mode/'model'
 for method,filename,field in [('initial','initial.json','ledger'),('round0','round0.json','ledger'),('final_shared','sketch.json','ledger'),('final_independent','sketch.json','independent_connection_ledger')]:
  q=W/filename;state=json.loads(q.read_text());bindings[str(q)]=sha(q);assert len(state['records'])==6273;ledger=state[field]
  pred={n:ledger.get(str(n),0) for n in caps};spred=Counter()
  for n,keys in incidence.items():
   for k in keys:spred[k]+=pred[n]
  predictions[mode+'/'+method]=(pred,{k:spred[k]/spcaps[k] for k in spcaps})
oracle=R/'tools/verify_aes_native_demand_span_ablation_hotspots_v1.py';fn=next(n for n in ast.parse(oracle.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='audit_metric');checked=0;exec(compile(ast.Module(body=[fn],type_ignores=[]),str(oracle),'exec'));bindings[str(oracle)]=sha(oracle)
rows=[]
for row in s['rows']:
 i=row['iteration'];q=L/'snapshot_audits_v2'/f'iteration_{i:03d}.json';assert sha(q)==s['bindings'][str(q)];a=json.loads(q.read_text());assert a['all_printed_branch_arc_switch_and_union_checks_pass'] and a['inputs_sha256']['graph']==ep['graph_sha256'];occupancy=a['node_occupancy'];truth={n:occupancy.get(str(n),0) for n in caps};over={n for n in truth if truth[n]>caps[n]};assert len(over)==row['overused_channel_nodes'];assert sum(max(0,truth[n]-caps[n]) for n in caps)==row['channel_overflow_units'];sptruth=Counter()
 for n,keys in incidence.items():
  for k in keys:sptruth[k]+=truth[n]
 spatial={k:sptruth[k]/spcaps[k] for k in spcaps};metrics={}
 for method,(pred,sppred) in predictions.items():
  cm=compare(pred,truth,1409);sm=compare(sppred,spatial,20);audit_metric(pred,truth,cm,1409);audit_metric(sppred,spatial,sm,20)
  positive={n for n in pred if pred[n]>caps[n]};tp=len(positive&over);fp=len(positive-over);fnc=len(over-positive);tn=len(caps)-tp-fp-fnc;assert min(tp,fp,fnc,tn)>=0
  classification=dict(tp=tp,fp=fp,fn=fnc,tn=tn,precision=tp/(tp+fp) if tp+fp else None,recall=tp/(tp+fnc) if tp+fnc else None,f1=2*tp/(2*tp+fp+fnc) if 2*tp+fp+fnc else None)
  metrics[method]=dict(concrete=cm,spatial=sm,overuse_classification=classification)
 rows.append(dict(iteration=i,truth_overused_channels=len(over),metrics=metrics));print('ALL FACTORS ITERATION',i,'audited',flush=True)
assert [r['iteration'] for r in rows]==list(range(1,19)) and checked==576 and all(sha(q)==h for q,h in bindings.items())
(D/'transient_comparison.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,independent_histogram_checks=checked,scope='Exploratory all18 original-cold physical snapshots/all16 frozen factor-representation vectors/all28188CHAN/all1680bins. Complete fixedtopk and native capacity-threshold overuse confusion matrices. Snapshots may be illegal intermediate routes; not route-failure labels, strictheldout, selected iteration/policy or speedgain proof.'),indent=2)+'\n');print('ALL TRANSIENT FACTORS PASS',checked)
