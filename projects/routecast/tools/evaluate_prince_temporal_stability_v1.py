"""Frozen grouped temporal owner stability forecast, original full-domain gates."""
import json,struct,hashlib
from pathlib import Path
from collections import Counter
from fractions import Fraction
from expected_channel_forecast_vectors_v1 import vectors
from external_forecast_metrics_v1 import vectors as physical,metrics,gate
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_temporal_stability_v1_2026-10-20'
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def word(x):return struct.unpack('<I',struct.pack('<f',float(x)))[0]
def value(x):return Fraction(struct.unpack('<f',struct.pack('<I',x))[0])
def main():
 frozen=load(D/'frozen_features.json');assert all(sha(p)==h for p,h in frozen['bindings'].items());bindings={str(D/'frozen_features.json'):sha(D/'frozen_features.json'),str(Path(__file__)):sha(__file__)};data={};domains={}
 for row in frozen['rows']:
  if row['status']!='FEATURES_FROZEN_NO_LABELS':continue
  c=row['case'];specp=E/'prince_feedback_quality_v1_2026-10-20'/c/'specification.json';spec=load(specp);lp=Path(spec['label_physical_audit']);truth={int(n):v for n,v in load(lp)['node_occupancy'].items()};data[c]={x['id']:(x['B'],x['P'],x['S'],truth.get(x['id'],0)) for x in map(json.loads,Path(row['features']).open())};assert all(x[3] in [0,1] for x in data[c].values());folder=E/'prince_quality_domains_v1_2026-10-20'/c.split('/')[0];rp=folder/'resources.jsonl';bp=folder/'spatial_bins.json';mp=folder/'verification.json';domains[c]=(list(map(json.loads,rp.open())),load(bp),load(mp),truth)
  for p in [specp,lp,rp,bp,mp,specp.parent/'comparison.json']:bindings[str(p)]=sha(p)
 folds=[];bycase={}
 for ep in ['episode_01','episode_02','episode_03']:
  train=sorted(c for c in data if c.split('/')[1]!=ep);test=sorted(set(data)-set(train));assert len(train)==4 and len(test)==2;counts=Counter();positive=Counter()
  for c in train:
   for b,p,s,y in data[c].values():
    for key in [(),(b,),(b,p),(b,p,s)]:counts[key]+=1;positive[key]+=y
  words={}
  for key in sorted(counts,key=lambda k:(len(k),k)):words[key]=word(Fraction(positive[key]+1,counts[key]+2))
  f=dict(heldout_episode=ep,train_cases=train,test_cases=test,cells={','.join(map(str,k)):dict(resources=n,occupied=positive[k],word=words[k]) for k,n in counts.items()});folds.append(f)
  for c in test:bycase[c]=words
 rows=[]
 for entry in frozen['rows']:
  c=entry['case']
  if c not in data:rows.append(dict(case=c,status=entry['status'],pass_both_controls=False));continue
  words=bycase[c];resources,bins,meta,truth=domains[c];pred={n:{} for n in ['B','BP','BPS']}
  for node,(b,p,s,y) in data[c].items():
   for name,key in [('B',(b,)),('BP',(b,p)),('BPS',(b,p,s))]:
    while key not in words:key=key[:-1]
    pred[name][node]=value(words[key])
  t=physical(resources,bins,truth,meta['graph_nodes'],truth=True);ms={n:metrics(vectors(resources,bins,p,meta['graph_nodes']),t,meta['resource_k'],meta['spatial_k']) for n,p in pred.items()};orig=load(E/'prince_feedback_quality_v1_2026-10-20'/c/'comparison.json');checks={n:{ctrl:gate(m,orig['metrics'][ctrl]) for ctrl in ['previous_native','raw_min_on']} for n,m in ms.items()};passed=all(x['pass_primary_gate'] for x in checks['BPS'].values());scorep=D/c/'expected_counts.jsonl'
  with scorep.open('x') as f:
   for node in data[c]:f.write(json.dumps(dict(id=node,**{n:word(p[node]) for n,p in pred.items()}))+'\n')
  bindings[str(scorep)]=sha(scorep);brier={n:float(sum((q-truth.get(node,0))**2 for node,q in p.items())/len(p)) for n,p in pred.items()};rows.append(dict(case=c,status='SCORED',metrics=ms,checks=checks,pass_both_controls=passed,Brier=brier));print(c,passed,{n:{s:(x['spearman'],x['top_k_hits']) for s,x in m.items()} for n,m in ms.items()},flush=True)
 assert all(sha(p)==h for p,h in bindings.items());modelp=D/'models.json'
 with modelp.open('x') as f:json.dump(dict(folds=folds),f,indent=2)
 bindings[str(modelp)]=sha(modelp)
 with (D/'verification.json').open('x') as f:json.dump(dict(status='GROUP_HELDOUT_TEMPORAL_STABILITY_SCORED',rows=rows,available_cases=6,required_cases=9,passed_available_cases=sum(r['pass_both_controls'] for r in rows),full9_gate=False,bindings=bindings,scope='Exposed development only; independent metric/model audit pending; no native/fullpaid/unseen claim.'),f,indent=2,default=lambda x:dict(numerator=x.numerator,denominator=x.denominator));f.write('\n')
if __name__=='__main__':main()
