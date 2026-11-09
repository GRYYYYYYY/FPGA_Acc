"""Independent direct-peer features, heldout cell counts, scores and transposed metrics."""
import json,struct,hashlib,math
from pathlib import Path
from fractions import Fraction
from collections import defaultdict,Counter
from audit_prince_forecast_metrics_v1 import check
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_local_history_v1_2026-10-20'
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def word(q):return struct.unpack('<I',struct.pack('<f',float(q)))[0]
def value(w):return Fraction(struct.unpack('<f',struct.pack('<I',w))[0])
def main():
 v=load(D/'verification.json');frozen=load(D/'frozen_features.json');assert all(sha(p)==h for p,h in v['bindings'].items());assert all(sha(p)==h for p,h in frozen['bindings'].items());data={};truths={};domains={};feature_count=0
 for row in frozen['rows']:
  if row['status']!='FEATURES_FROZEN_NO_LABELS':continue
  c=row['case'];src=E/'prince_input_mean_trial_v1_2026-10-20'/c/'identity';hist=[]
  for it in row['iterations']:
   raw=(src/'boundary'/f'iteration_{it}.bin').read_bytes();assert raw[:8]==b'RCBND001' and struct.unpack_from('<Q',raw,8)[0]==it;hist.append({n:int(occ>0) for n,kind,occ,cap,acc in struct.iter_unpack('<QIiiI',raw[24:])})
  folder=E/'prince_quality_domains_v1_2026-10-20'/c.split('/')[0];resources=list(map(json.loads,(folder/'resources.jsonl').open()));bins=load(folder/'spatial_bins.json');meta=load(folder/'verification.json');adj=defaultdict(list)
  for r in resources:
   for key in r['bins']:adj[tuple(key)].append(r['id'])
  features={x['id']:x for x in map(json.loads,Path(row['features']).open())};assert len(features)==len(resources) and set(features)=={r['id'] for r in resources}
  for r in resources:
   n=r['id'];pattern=sum(hist[i][n]*(2**i) for i in range(3));fractions=[]
   for key in r['bins']:
    peers=[other for other in adj[tuple(key)] if other!=n];assert len(peers)==len(adj[tuple(key)])-1;fractions.append(Fraction(sum(hist[0][other] for other in peers),len(peers)))
   density=sum(fractions,Fraction())/len(fractions);quantile=min(3,math.floor(4*density));assert features[n]==dict(id=n,T=pattern,Q=quantile,peer_density_numerator=density.numerator,peer_density_denominator=density.denominator);feature_count+=1
  data[c]=features;spec=load(E/'prince_feedback_quality_v1_2026-10-20'/c/'specification.json');truths[c]={int(n):y for n,y in load(spec['label_physical_audit'])['node_occupancy'].items()};domains[c]=(resources,bins,meta,adj)
 models={};model_cells=0
 for fold in load(D/'models.json')['folds']:
  train=sorted(c for c in data if c.split('/')[1]!=fold['heldout_episode']);test=sorted(set(data)-set(train));assert train==fold['train_cases'] and test==fold['test_cases'] and len(train)==4 and len(test)==2;cnt=Counter();positive=Counter()
  for c in train:
   for n,x in data[c].items():
    t,d=x['T'],x['Q'];keys=['G',f'B/{t%2}',f'BP/{t%4}',f'T/{t}',f'BPQ/{t%4}/{d}',f'TQ/{t}/{d}']
    for k in keys:cnt[k]+=1;positive[k]+=truths[c].get(n,0)
  assert set(cnt)==set(fold['cells']);words={}
  for k,num in cnt.items():
   w=word(Fraction(positive[k]+1,num+2));assert fold['cells'][k]==dict(resources=num,occupied=positive[k],word=w);words[k]=w;model_cells+=1
  for c in test:models[c]=words
 vectors=gates=0
 for row in v['rows']:
  if row['status']!='SCORED':continue
  c=row['case'];resources,bins,meta,adj=domains[c];cap={r['id']:r['capacity'] for r in resources};bc={tuple(b['key']):b['capacity'] for b in bins};scores={x['id']:x for x in map(json.loads,Path(row['score_file']).open())};assert set(scores)==set(data[c]);pred={name:{} for name in ['BP','T','BPQ','TQ']}
  for n,x in data[c].items():
   t,d=x['T'],x['Q'];base=[f'BP/{t%4}',f'B/{t%2}','G'];chains=dict(BP=base,T=[f'T/{t}']+base,BPQ=[f'BPQ/{t%4}/{d}']+base,TQ=[f'TQ/{t}/{d}',f'T/{t}']+base)
   for name,keys in chains.items():
    w=next(models[c][k] for k in keys if k in models[c]);assert scores[n][name]==w;pred[name][n]=value(w)
  def normalize(p):return dict(resource={n:Fraction(p.get(n,0))/ca for n,ca in cap.items()},spatial={k:sum((Fraction(p.get(n,0)) for n in members),Fraction())/bc[k] for k,members in adj.items()})
  truth=truths[c];target=normalize(truth);orig=load(E/'prince_feedback_quality_v1_2026-10-20'/c/'comparison.json')
  for name,p in pred.items():
   normalized=normalize(p)
   for scope,k in [('resource',meta['resource_k']),('spatial',meta['spatial_k'])]:check(normalized[scope],target[scope],k,row['metrics'][name][scope]);vectors+=1
   brier=float(sum((x-truth.get(n,0))**2 for n,x in p.items())/len(p));assert brier==row['Brier'][name]
   for ctrl in ['previous_native','raw_min_on']:
    nr=[];strict=[]
    for scope in ['resource','spatial']:
     a=row['metrics'][name][scope];b=orig['metrics'][ctrl][scope];nr.extend([a['spearman']>=b['spearman']-1e-12,a['top_k_hits']>=b['top_k_hits']]);strict.extend([a['spearman']>b['spearman']+1e-12,a['top_k_hits']>b['top_k_hits']])
    assert (all(nr) and any(strict))==row['checks'][name][ctrl]['pass_primary_gate'];gates+=1
  assert all(x['pass_primary_gate'] for x in row['checks']['TQ'].values())==row['pass_both_controls']
  print('INDEPENDENT_LOCAL_HISTORY',c,flush=True)
 assert len(v['rows'])==9 and vectors==48 and gates==48 and feature_count==89280
 out=dict(status='DIRECT_PEERS_MODELS48_METRIC_VECTORS48_GATES_RECONCILED',feature_resources=feature_count,model_cells=model_cells,metric_vectors=vectors,control_gates=gates,source_sha256=sha(D/'verification.json'),auditor_sha256=sha(__file__),scope='All resource features from independently enumerated excluded-self peers and native three-phase snapshots; independent fold counts/words/scores/rank metrics/control gates. Development exposed; original full9=false.')
 with (D/'independent_verification_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print(out['status'])
if __name__=='__main__':main()
