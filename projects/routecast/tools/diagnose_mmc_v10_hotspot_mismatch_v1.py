"""Authenticated descriptive strata, rank trajectories and original physical hotspot support."""
import json,sys,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from prediction_metrics import compare
D=R/'experiments/mmc_v10_feedback_hotspots_v2_2026-10-09/mmc'
bindings=closure([Path(__file__)])
for filename in ['metric_verification.json','truth_tie_sensitivity.json']:
 p=D/filename;r=json.loads(p.read_text());assert all(sha(k)==h for k,h in r['bindings'].items());bindings.update(r['bindings']);bindings[str(p)]=sha(p)
vp=D/'comparison_vectors.json';v=json.loads(vp.read_text());bindings[str(vp)]=sha(vp)
bins=v['bins'];channels={x['node']:x for x in v['channels']};by=defaultdict(list)
for b in bins:by[b['key'][3],b['key'][4]].append(b)
methods=['rc_initial','round0_shared','final_shared','final_independent','geometry']
def score(b,m):return b['geometry'] if m=='geometry' else b['predictions'][m]/b['capacity']
truth={tuple(b['key']):b['native']/b['capacity'] for b in bins}
ordered_truth=sorted(bins,key=lambda b:(-truth[tuple(b['key'])],b['key']))
rankings={m:{tuple(b['key']):i+1 for i,b in enumerate(sorted(bins,key=lambda b:(-score(b,m),b['key'])))} for m in methods}
strata=[]
for (kind,segment),bs in sorted(by.items()):
 t={tuple(b['key']):truth[tuple(b['key'])] for b in bs};metrics={}
 for m in methods:
  p={tuple(b['key']):score(b,m) for b in bs}
  metrics[m]=dict(compare(p,t,20),signed_mean_error=sum(p[k]-t[k] for k in t)/len(t))
 strata.append(dict(type=kind,segment_id=segment,bins=len(bs),capacity_sum=sum(b['capacity'] for b in bs),native_occupancy_sum=sum(b['native'] for b in bs),metrics=metrics))
top=ordered_truth[:20];wanted={tuple(b['key']) for b in top};support={k:[] for k in wanted}
epfile=R/'experiments/ultraembedded_mmc_continuous_workflow_v10_2026-10-09/seed/demand/mmc/endpoints.json';ep=json.loads(epfile.read_text());graph=Path(ep['inputs']['graph']['path']);assert sha(graph)==ep['graph_sha256'];stack=[]
for event,e in ET.iterparse(graph,events=('start','end')):
 if event=='start':stack.append(e);continue
 if e.tag=='node':
  n=int(e.get('id'))
  if n in channels:
   loc=e.find('loc');segment=e.find('segment');sid=int(segment.get('segment_id')) if segment is not None else -1
   for k in wanted:
    layer,x,y,kind,seg=k
    if kind==e.get('type') and sid==seg and layer==int(loc.get('layer','0')) and int(loc.get('xlow'))<=x<=int(loc.get('xhigh')) and int(loc.get('ylow'))<=y<=int(loc.get('yhigh')):support[k].append(n)
 if e.tag in {'node','edge'}:
  if len(stack)>1:stack[-2].remove(e)
  e.clear()
 stack.pop()
groups=defaultdict(list);hotspots=[]
for b in top:
 k=tuple(b['key']);ids=sorted(support[k]);cs=[channels[n] for n in ids];assert ids and sum(c['capacity'] for c in cs)==b['capacity'] and sum(c['native'] for c in cs)==b['native']
 for m in b['predictions']:assert sum(c['predictions'][m] for c in cs)==b['predictions'][m]
 groups[tuple(ids)].append(list(k))
 hotspots.append(dict(key=list(k),physical_nodes=ids,capacity=b['capacity'],native_utilization=truth[k],predicted_utilization={m:score(b,m) for m in methods},predicted_rank={m:rankings[m][k] for m in methods}))
predicted_hotspots={m:[dict(key=b['key'],predicted_utilization=score(b,m),native_utilization=truth[tuple(b['key'])]) for b in sorted(bins,key=lambda b:(-score(b,m),b['key']))[:20]] for m in methods}
summary={m:dict(true_top20_mean_prediction_rank=sum(x['predicted_rank'][m] for x in hotspots)/20,true_top20_mean_predicted_utilization=sum(x['predicted_utilization'][m] for x in hotspots)/20,predicted_top20_mean_native_utilization=sum(x['native_utilization'] for x in predicted_hotspots[m])/20) for m in methods}
for p in [epfile,graph]:bindings[str(p)]=sha(p)
assert all(sha(k)==h for k,h in bindings.items())
result=dict(bindings=bindings,strata=strata,true_top20=hotspots,predicted_top20=predicted_hotspots,summary=summary,distinct_physical_support_sets=len(groups),repeated_support_groups=[dict(keys=ks,physical_nodes=list(ids)) for ids,ks in groups.items() if len(ks)>1],scope='Post-outcome development diagnosis; original XML support verified on fixed true top20 bins, complete spatial strata and rank trajectories. Diagnostic stratum top20 does not replace primary full-universe metrics. Rank uses deterministic ID tie rule; previously published tie limits remain. No hidden k changes, unseen-family/routability/causal/native timing claims.')
(D/'hotspot_mismatch_diagnosis.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(summary=summary,distinct_physical_support_sets=len(groups),strata=[dict(type=s['type'],segment=s['segment_id'],bins=s['bins'],spearman={m:x['spearman'] for m,x in s['metrics'].items()}) for s in strata]),indent=2),flush=True)
