import json,sys,math
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
out=R/'experiments/aes_feedback_round_ablation_v1_2026-10-08';p=out/'resource_strata_diagnosis.json';d=json.loads(p.read_text());assert all(sha(k)==v for k,v in d['bindings'].items());bindings={str(p):sha(p),str(Path(__file__)):sha(Path(__file__))};checked=0
for row in d['rows']:
 v=out/row['name']/'comparison_vectors.json';data=json.loads(v.read_text());bindings[str(v)]=sha(v);bins=data['bins'];channels={x['node']:x for x in data['channels']};seen=set()
 for s in row['strata']:
  bs=[b for b in bins if b['key'][3]==s['type'] and b['key'][4]==s['segment_id']];ids=[tuple(b['key']) for b in bs];assert not seen.intersection(ids);seen.update(ids);assert len(bs)==s['spatial_bins']
  assert sum(b['capacity'] for b in bs)==s['capacity_sum'] and sum(b['native'] for b in bs)==s['native_spatial_occupancy_sum']
  truth={tuple(b['key']):b['native']/b['capacity'] for b in bs}
  def ranks(v):
   h=Counter(v.values());n=0;rank={}
   for x,c in sorted(h.items()):rank[x]=n+(c-1)/2;n+=c
   return {k:rank[x] for k,x in v.items()}
  for method,m in s['metrics'].items():
   pred={tuple(b['key']):b['predictions'][method]/b['capacity'] for b in bs};a=ranks(pred);b=ranks(truth);mu=(len(bs)-1)/2
   corr=sum((a[k]-mu)*(b[k]-mu) for k in ids)/math.sqrt(sum((x-mu)**2 for x in a.values())*sum((x-mu)**2 for x in b.values()))
   assert abs(corr-m['spearman'])<1e-12 and abs(sum(abs(pred[k]-truth[k]) for k in ids)/len(ids)-m['mae'])<1e-12
   ps=sorted(ids,key=lambda k:(-pred[k],k))[:20];ts=sorted(ids,key=lambda k:(-truth[k],k))[:20];assert len(set(ps)&set(ts))/20==m['precision_at_k']==m['recall_at_k']
   assert abs(sum(pred[k]-truth[k] for k in ids)/len(ids)-m['signed_mean_error'])<1e-12
   assert sum(x['predictions'][method] for x in bs)==m['prediction_spatial_occupancy_sum'];checked+=1
 assert seen=={tuple(b['key']) for b in bins}
 top=sorted(bins,key=lambda b:(-b['native']/b['capacity'],b['key']))[:20];assert [x['key'] for x in row['true_top20']]==[x['key'] for x in top]
 support={}
 for h in row['true_top20']:
  nodes=h['physical_nodes'];assert len(set(nodes))==len(nodes);cs=[channels[n] for n in nodes]
  assert sum(x['capacity'] for x in cs)==h['capacity'] and sum(x['native'] for x in cs)==h['native']
  for method,value in h['predictions'].items():assert sum(x['predictions'][method] for x in cs)==value
  support.setdefault(tuple(nodes),[]).append(h['key'])
 assert len(support)==row['distinct_physical_support_sets']
 assert row['repeated_support_groups']==[dict(keys=keys,physical_nodes=list(nodes)) for nodes,keys in support.items() if len(keys)>1]
assert checked==24 and all(sha(k)==v for k,v in bindings.items())
(out/'resource_strata_verification.json').write_text(json.dumps(dict(bindings=bindings,metric_groups=checked,full_stratum_partition_metrics_and_support_aggregation_pass=True,scope='Independent histogram/MAE/topk recomputation and complete partition/support aggregation. Original XML support membership checked by producer; no second XML membership proof claimed.'),indent=2)+'\n');print('PASS',checked)
