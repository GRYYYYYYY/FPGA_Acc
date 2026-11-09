"""Descriptive full-universe strata and physical support of true hotspot bins."""
import json,sys,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from prediction_metrics import compare
out=R/'experiments/aes_feedback_round_ablation_v1_2026-10-08'
bindings={str(Path(__file__)):sha(Path(__file__))}
for file in ['vector_verification.json','metric_verification.json']:
 p=out/file;d=json.loads(p.read_text());assert all(sha(k)==v for k,v in d['bindings'].items());bindings[str(p)]=sha(p)
rows=[]
for name in ['aes_cipher','aes_inv_cipher']:
 p=out/name/'comparison_vectors.json';data=json.loads(p.read_text());bindings[str(p)]=sha(p);bins=data['bins'];by=defaultdict(list)
 for b in bins:by[b['key'][3],b['key'][4]].append(b)
 strata=[]
 for (kind,segment),bs in sorted(by.items()):
  truth={tuple(b['key']):b['native']/b['capacity'] for b in bs};metrics={}
  for method in ['rc_initial','wire_round0','wire_shared']:
   pred={tuple(b['key']):b['predictions'][method]/b['capacity'] for b in bs}
   metrics[method]=dict(compare(pred,truth,20),signed_mean_error=sum(pred[k]-truth[k] for k in truth)/len(truth),prediction_spatial_occupancy_sum=sum(b['predictions'][method] for b in bs))
  strata.append(dict(type=kind,segment_id=segment,spatial_bins=len(bs),capacity_sum=sum(b['capacity'] for b in bs),native_spatial_occupancy_sum=sum(b['native'] for b in bs),metrics=metrics))
 top=sorted(bins,key=lambda b:(-b['native']/b['capacity'],b['key']))[:20];wanted={tuple(b['key']) for b in top};support={k:[] for k in wanted}
 epfile=R/'experiments/aes_native_demand_frontend_v1_2026-10-08'/name/'endpoints.json';ep=json.loads(epfile.read_text());graph=Path(ep['inputs']['graph']['path']);assert sha(graph)==ep['graph_sha256'];channels={c['node']:c for c in data['channels']};stack=[]
 for event,el in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(el);continue
  if el.tag=='node':
   n=int(el.get('id'))
   if n in channels:
    loc=el.find('loc');seg=el.find('segment');sid=int(seg.get('segment_id')) if seg is not None else -1
    for k in wanted:
     layer,x,y,kind,segment=k
     if kind==el.get('type') and sid==segment and layer==int(loc.get('layer','0')) and int(loc.get('xlow'))<=x<=int(loc.get('xhigh')) and int(loc.get('ylow'))<=y<=int(loc.get('yhigh')):support[k].append(n)
  # Preserve node children until node end; release all complete nodes and edges.
  if el.tag in {'node','edge'}:
   if len(stack)>1:stack[-2].remove(el)
   el.clear()
  stack.pop()
 groups=defaultdict(list);hotspots=[]
 for b in top:
  k=tuple(b['key']);ids=sorted(support[k]);cs=[channels[n] for n in ids];assert ids and sum(c['capacity'] for c in cs)==b['capacity'] and sum(c['native'] for c in cs)==b['native']
  for m in b['predictions']:assert sum(c['predictions'][m] for c in cs)==b['predictions'][m]
  groups[tuple(ids)].append(list(k));hotspots.append(dict(key=list(k),physical_nodes=ids,native=b['native'],capacity=b['capacity'],predictions=b['predictions']))
 for p in [epfile,graph]:bindings[str(p)]=sha(p)
 rows.append(dict(name=name,strata=strata,true_top20=hotspots,distinct_physical_support_sets=len(groups),repeated_support_groups=[dict(keys=keys,physical_nodes=list(ids)) for ids,keys in groups.items() if len(keys)>1]))
assert all(sha(k)==v for k,v in bindings.items())
(out/'resource_strata_diagnosis.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Full descriptive spatial strata and original XML support verification. Repeated bins can share identical physical resources; do not treat them as independent hotspots. No cost/model changes, heldout validation or native QoR inference.'),indent=2)+'\n')
for row in rows:
 print(row['name'],'distinct top20 physical support',row['distinct_physical_support_sets'],'repeated',[(len(g['keys']),len(g['physical_nodes'])) for g in row['repeated_support_groups']])
 for s in row['strata']:print(s['type'],s['segment_id'],{m:(round(v['spearman'],4),v['precision_at_k'],round(v['signed_mean_error'],4)) for m,v in s['metrics'].items()})
