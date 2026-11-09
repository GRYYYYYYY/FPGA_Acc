"""Independent full-domain model reconstruction and transposed metric audit."""
import json,struct,hashlib
from pathlib import Path
from fractions import Fraction
from collections import defaultdict,Counter
from audit_prince_forecast_metrics_v1 import check
R=Path(__file__).resolve().parents[1];D=R/'experiments/prince_full_resource_history_v1_2026-10-20'
def load(p):return json.loads(Path(p).read_text())
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def word(q):return struct.unpack('<I',struct.pack('<f',float(q)))[0]
def q(w):return Fraction(struct.unpack('<f',struct.pack('<I',w))[0])
def main():
 v=load(D/'verification.json');assert all(digest(p)==h for p,h in v['bindings'].items());assert digest(D/'models.json')==v['models_sha256'] and digest(D/'frozen_features.json')==v['frozen_features_sha256'];data={};domains={}
 for row in v['rows']:
  if row['status']!='SCORED':continue
  c=row['case'];src=R/'experiments/prince_input_mean_trial_v1_2026-10-20'/c/'identity';raw=(src/'callback.tsv.ready_RR.bin').read_bytes();assert raw[:8]==b'RCBND001';rr={n:(kind,occ,cap,acc) for n,kind,occ,cap,acc in struct.iter_unpack('<QIiiI',raw[24:])};folder=R/'experiments/prince_quality_domains_v1_2026-10-20'/c.split('/')[0];resources=list(map(json.loads,(folder/'resources.jsonl').open()));bins=load(folder/'spatial_bins.json');meta=load(folder/'verification.json');spec=load(R/'experiments/prince_feedback_quality_v1_2026-10-20'/c/'specification.json');truth={int(n):x for n,x in load(spec['label_physical_audit'])['node_occupancy'].items()};features={x['id']:x for x in map(json.loads,(D/c/'input_features.jsonl').open())};assert set(features)=={r['id'] for r in resources};data[c]={}
  for r in resources:
   n=r['id'];kind,occ,cap,acc=rr[n];b=int(occ>0);h=int(q(acc)>1);assert features[n]==dict(id=n,B=b,H=h,native_count=occ,acc_bits=acc);assert truth.get(n,0) in [0,1];data[c][n]=(b,h,truth.get(n,0),occ)
  domains[c]=(resources,bins,meta,truth)
 models={}
 for f in load(D/'models.json')['folds']:
  train=sorted(c for c in data if c.split('/')[1]!=f['heldout_episode']);test=sorted(set(data)-set(train));assert train==f['train_cases'] and test==f['test_cases'] and len(train)==4 and len(test)==2;cnt=Counter();pos=Counter()
  for c in train:
   for b,h,y,occ in data[c].values():cnt[b,h]+=1;pos[b,h]+=y
  for b in [0,1]:
   bn=sum(cnt[b,h] for h in [0,1]);bp=sum(pos[b,h] for h in [0,1]);assert f['B_words'][str(b)]==word(Fraction(bp+1,bn+2))
   for h in [0,1]:assert f['cell_counts'][f'{b},{h}']==dict(resources=cnt[b,h],occupied=pos[b,h]) and f['BH_words'][f'{b},{h}']==word(Fraction(pos[b,h]+1,cnt[b,h]+2))
  for c in test:models[c]=f
 rows=[];vectors=0
 for row in v['rows']:
  if row['status']!='SCORED':continue
  c=row['case'];resources,bins,meta,truth=domains[c];f=models[c];adj=defaultdict(list);cap={r['id']:r['capacity'] for r in resources};bc={tuple(b['key']):b['capacity'] for b in bins}
  for r in resources:
   for key in r['bins']:adj[tuple(key)].append(r['id'])
  def norm(vals):return dict(resource={n:Fraction(vals.get(n,0))/cap[n] for n in cap},spatial={key:sum((Fraction(vals.get(n,0)) for n in ns),Fraction())/bc[key] for key,ns in adj.items()})
  pred={name:{} for name in ['native_ready','clipped_ready','B_only','BH']}
  scores={x['id']:x for x in map(json.loads,(D/c/'expected_counts.jsonl').open())};assert set(scores)==set(cap)
  for n,(b,h,y,occ) in data[c].items():
   assert scores[n]==dict(id=n,B=b,H=h,B_word=f['B_words'][str(b)],BH_word=f['BH_words'][f'{b},{h}']);pred['native_ready'][n]=occ;pred['clipped_ready'][n]=b;pred['B_only'][n]=q(scores[n]['B_word']);pred['BH'][n]=q(scores[n]['BH_word'])
  t=norm(truth)
  for name,p in pred.items():
   out=norm(p)
   for scope,k in [('resource',meta['resource_k']),('spatial',meta['spatial_k'])]:check(out[scope],t[scope],k,row['metrics'][name][scope]);vectors+=1
  original=load(R/'experiments/prince_feedback_quality_v1_2026-10-20'/c/'comparison.json');gates={}
  for control in ['previous_native','raw_min_on']:
   nr=[];strict=[]
   for scope in ['resource','spatial']:
    a=row['metrics']['BH'][scope];b=original['metrics'][control][scope];nr.extend([a['spearman']>=b['spearman']-1e-12,a['top_k_hits']>=b['top_k_hits']]);strict.extend([a['spearman']>b['spearman']+1e-12,a['top_k_hits']>b['top_k_hits']])
   gates[control]=all(nr) and any(strict);assert gates[control]==row['checks'][control]['pass_primary_gate']
  assert all(gates.values())==row['pass_both_controls'];rows.append(dict(case=c,gates=gates))
 assert vectors==48 and len(v['rows'])==9
 out=dict(status='INDEPENDENT_FEATURE_MODEL_AND48_METRIC_VECTORS_PASS',metric_vectors=vectors,rows=rows,source_sha256=digest(D/'verification.json'),auditor_sha256=digest(__file__),full9_gate=False)
 with (D/'independent_verification_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print(out['status'])
if __name__=='__main__':main()
