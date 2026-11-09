"""Independent grouped cell reconstruction and transposed metric verification."""
import json,hashlib,struct
from pathlib import Path
from fractions import Fraction
from collections import Counter,defaultdict
from audit_prince_forecast_metrics_v1 import check
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_temporal_stability_v1_2026-10-20'
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def word(q):return struct.unpack('<I',struct.pack('<f',float(q)))[0]
def val(w):return Fraction(struct.unpack('<f',struct.pack('<I',w))[0])
def main():
 v=load(D/'verification.json');assert all(sha(p)==h for p,h in v['bindings'].items());data={};truths={}
 for row in v['rows']:
  if row['status']!='SCORED':continue
  c=row['case'];spec=load(E/'prince_feedback_quality_v1_2026-10-20'/c/'specification.json');truths[c]={int(n):y for n,y in load(spec['label_physical_audit'])['node_occupancy'].items()};data[c]=list(map(json.loads,(D/c/'input_features.jsonl').open()))
 models={}
 for fold in load(D/'models.json')['folds']:
  train=sorted(c for c in data if c.split('/')[1]!=fold['heldout_episode']);assert train==fold['train_cases'];assert sorted(set(data)-set(train))==fold['test_cases'];counts=Counter();positive=Counter()
  for c in train:
   for x in data[c]:
    key=(x['B'],x['P'],x['S'])
    for size in range(4):counts[key[:size]]+=1;positive[key[:size]]+=truths[c].get(x['id'],0)
  model={}
  for k,n in counts.items():
   w=word(Fraction(positive[k]+1,n+2));assert fold['cells'][','.join(map(str,k))]==dict(resources=n,occupied=positive[k],word=w);model[k]=w
  assert len(fold['cells'])==len(counts)
  for c in fold['test_cases']:models[c]=model
 vectors=0;gates=0
 for row in v['rows']:
  if row['status']!='SCORED':continue
  c=row['case'];folder=E/'prince_quality_domains_v1_2026-10-20'/c.split('/')[0];resources=list(map(json.loads,(folder/'resources.jsonl').open()));bins=load(folder/'spatial_bins.json');meta=load(folder/'verification.json');adj=defaultdict(list);caps={r['id']:r['capacity'] for r in resources};bc={tuple(b['key']):b['capacity'] for b in bins}
  for r in resources:
   for key in r['bins']:adj[tuple(key)].append(r['id'])
  def norm(p):return dict(resource={n:Fraction(p.get(n,0))/cap for n,cap in caps.items()},spatial={k:sum((Fraction(p.get(n,0)) for n in ns),Fraction())/bc[k] for k,ns in adj.items()})
  scores={x['id']:x for x in map(json.loads,(D/c/'expected_counts.jsonl').open())};assert set(scores)==set(caps);pred={name:{} for name in ['B','BP','BPS']}
  for x in data[c]:
   for name,size in [('B',1),('BP',2),('BPS',3)]:
    key=(x['B'],x['P'],x['S'])[:size]
    while key not in models[c]:key=key[:-1]
    w=models[c][key];assert scores[x['id']][name]==w;pred[name][x['id']]=val(w)
  t=norm(truths[c]);orig=load(E/'prince_feedback_quality_v1_2026-10-20'/c/'comparison.json')
  for name,p in pred.items():
   out=norm(p)
   for scope,k in [('resource',meta['resource_k']),('spatial',meta['spatial_k'])]:check(out[scope],t[scope],k,row['metrics'][name][scope]);vectors+=1
   for ctrl in ['previous_native','raw_min_on']:
    nr=[];strict=[]
    for scope in ['resource','spatial']:
     a=row['metrics'][name][scope];b=orig['metrics'][ctrl][scope];nr.extend([a['spearman']>=b['spearman']-1e-12,a['top_k_hits']>=b['top_k_hits']]);strict.extend([a['spearman']>b['spearman']+1e-12,a['top_k_hits']>b['top_k_hits']])
    assert (all(nr) and any(strict))==row['checks'][name][ctrl]['pass_primary_gate'];gates+=1
 assert vectors==36 and gates==36
 with (D/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='MODELS36_METRIC_VECTORS36_GATES_INDEPENDENTLY_RECONCILED',metric_vectors=vectors,control_gates=gates,source_sha256=sha(D/'verification.json'),auditor_sha256=sha(__file__),scope='Input owner/RR consistency from frozen producer; model/score/metrics/gates independently recomputed here. No unseen/native/fullpaid claim.'),f,indent=2)
 print('INDEPENDENT_TEMPORAL_PASS',vectors,gates)
if __name__=='__main__':main()
