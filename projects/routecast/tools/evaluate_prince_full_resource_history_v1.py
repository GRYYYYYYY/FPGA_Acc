"""Fixed full-resource (ready footprint,native elevated history) grouped posterior forecast."""
import json,struct,math,time
from pathlib import Path
from collections import Counter
from fractions import Fraction
from pre_route_endpoints import sha
from expected_channel_forecast_vectors_v1 import vectors as forecast_vectors
from external_forecast_metrics_v1 import vectors as native_vectors,metrics,gate
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_full_resource_history_v1_2026-10-20';S=E/'prince_input_mean_trial_v1_2026-10-20'
def number(word):return struct.unpack('<f',struct.pack('<I',word))[0]
def word(q):return struct.unpack('<I',struct.pack('<f',float(q)))[0]
def rational(word):return Fraction(number(word))
def encode(x):return json.loads(json.dumps(x,default=lambda f:dict(numerator=f.numerator,denominator=f.denominator)))
def fit(cases,data):
 cells=Counter();positive=Counter();base=Counter();base_positive=Counter()
 for case in cases:
  for n,(b,h,y) in data[case].items():cells[b,h]+=1;positive[b,h]+=y;base[b]+=1;base_positive[b]+=y
 total=sum(base.values());positives=sum(base_positive.values());bwords={};bhwords={}
 for b in [0,1]:
  q=Fraction(base_positive[b]+1,base[b]+2) if base[b] else Fraction(positives+1,total+2);bwords[str(b)]=word(q)
  for h in [0,1]:bhwords[f'{b},{h}']=word(Fraction(positive[b,h]+1,cells[b,h]+2)) if cells[b,h] else bwords[str(b)]
 return dict(train_cases=cases,B_words=bwords,BH_words=bhwords,cell_counts={f'{b},{h}':dict(resources=cells[b,h],occupied=positive[b,h]) for b in [0,1] for h in [0,1]})
def main():
 D.mkdir(exist_ok=False);tick=time.perf_counter();design=S/'full_resource_history_forecast_design_v1.json';bindings={str(p):sha(p) for p in [design,Path(__file__),R/'tools/expected_channel_forecast_vectors_v1.py',R/'tools/external_forecast_metrics_v1.py']};(D/'protocol.json').write_text(json.dumps(dict(design=json.loads(design.read_text()),bindings=dict(bindings),scope='Full resource-domain forecast,read-only unchanged-native-policy snapshots. Sparse-query calibration not reused as global probabilities.'),indent=2)+'\n');inputs=[];features={};domains={}
 for w in [96,128,160]:
  for ep in range(1,4):
   case=f'w{w:03d}/episode_{ep:02d}';src=S/case/'identity';ready=src/'callback.tsv.ready.tsv';events=[int(x.split()[0]) for x in ready.read_text().splitlines() if int(x.split()[4])];bindings[str(ready)]=sha(ready)
   if not events:inputs.append(dict(case=case,status='NO_READY_EVENT_OR_LEGAL_FINAL_LABEL'));continue
   assert len(events)==1;i=events[0];rp=E/'prince_quality_domains_v1_2026-10-20'/f'w{w:03d}'/'resources.jsonl';bp=rp.parent/'spatial_bins.json';dp=rp.parent/'verification.json';meta=json.loads(dp.read_text());resources=list(map(json.loads,rp.open()));bins=json.loads(bp.read_text());snap=src/'callback.tsv.ready_RR.bin';raw=snap.read_bytes();assert raw[:8]==b'RCBND001' and struct.unpack_from('<QQ',raw,8)==(i,meta['graph_nodes']);rr={n:(kind,occ,cap,acc) for n,kind,occ,cap,acc in struct.iter_unpack('<QIiiI',raw[24:])};folder=D/case;folder.mkdir(parents=True);path=folder/'input_features.jsonl';local={}
   with path.open('x') as f:
    for r in resources:
     n=r['id'];kind,occ,cap,acc=rr[n];a=number(acc);assert kind in [4,5] and cap==r['capacity']==1 and occ>=0 and math.isfinite(a) and a>=1;b=int(occ>0);h=int(a>1);local[n]=(b,h,occ);f.write(json.dumps(dict(id=n,B=b,H=h,native_count=occ,acc_bits=acc),separators=(',',':'))+'\n')
   features[case]=local;domains[case]=(resources,bins,meta);inputs.append(dict(case=case,status='FEATURES_READY',iteration=i,features=str(path),sha256=sha(path),resources=len(resources)));bindings[str(path)]=sha(path)
   for p in [rp,bp,dp,snap,src/'identity.txt']:bindings[str(p)]=sha(p)
 frozen=D/'frozen_features.json';frozen.write_text(json.dumps(dict(rows=inputs,bindings=dict(bindings)),indent=2)+'\n');frozen_hash=sha(frozen);data={};truths={};specs={}
 for case,local in features.items():
  spec=E/'prince_feedback_quality_v1_2026-10-20'/case/'specification.json';s=json.loads(spec.read_text());label=Path(s['label_physical_audit']);truth={int(n):v for n,v in json.loads(label.read_text())['node_occupancy'].items()};assert all(truth.get(n,0) in [0,1] for n in local);data[case]={n:(b,h,truth.get(n,0)) for n,(b,h,occ) in local.items()};truths[case]=truth;specs[case]=spec
  for p in [spec,label,spec.parent/'comparison.json']:bindings[str(p)]=sha(p)
 folds=[];models={}
 for group in ['episode_01','episode_02','episode_03']:
  train=sorted(case for case in data if case.split('/')[1]!=group);test=sorted(set(data)-set(train));assert len(train)==4 and len(test)==2;model=fit(train,data);model.update(heldout_episode=group,test_cases=test);folds.append(model)
  for case in test:models[case]=model
 rows=[]
 for entry in inputs:
  case=entry['case']
  if case not in data:rows.append(dict(case=case,status=entry['status'],pass_both_controls=False));continue
  resources,bins,meta=domains[case];truth=truths[case];model=models[case];bas={n:features[case][n][0] for n in features[case]};raw={n:features[case][n][2] for n in features[case]};B={n:rational(model['B_words'][str(b)]) for n,(b,h,y) in data[case].items()};BH={n:rational(model['BH_words'][f'{b},{h}']) for n,(b,h,y) in data[case].items()};labels=native_vectors(resources,bins,truth,meta['graph_nodes'],truth=True);predictions=dict(native_ready=native_vectors(resources,bins,raw,meta['graph_nodes']),clipped_ready=native_vectors(resources,bins,bas,meta['graph_nodes']),B_only=forecast_vectors(resources,bins,B,meta['graph_nodes']),BH=forecast_vectors(resources,bins,BH,meta['graph_nodes']));results={name:metrics(vec,labels,meta['resource_k'],meta['spatial_k']) for name,vec in predictions.items()};original=json.loads((specs[case].parent/'comparison.json').read_text());checks={name:gate(results['BH'],original['metrics'][name]) for name in ['previous_native','raw_min_on']};passed=all(x['pass_primary_gate'] for x in checks.values());assert rational(model['B_words']['1'])>rational(model['B_words']['0'])
  for scope in ['resource','spatial']:
   a,b=results['B_only'][scope],results['clipped_ready'][scope];assert a['spearman']==b['spearman'] and a['top_k_hits']==b['top_k_hits'] and a['prediction_top_k']==b['prediction_top_k']
  scorefile=D/case/'expected_counts.jsonl'
  with scorefile.open('x') as f:
   for n,(b,h,y) in data[case].items():f.write(json.dumps(dict(id=n,B=b,H=h,B_word=model['B_words'][str(b)],BH_word=model['BH_words'][f'{b},{h}']),separators=(',',':'))+'\n')
  brier={name:float(sum((q[n]-truth.get(n,0))**2 for n in data[case])/len(data[case])) for name,q in [('B_only',B),('BH',BH)]};rows.append(dict(case=case,status='SCORED',iteration=entry['iteration'],heldout_episode=model['heldout_episode'],metrics=results,checks=checks,pass_both_controls=passed,Brier=brier,score_file=str(scorefile),score_sha256=sha(scorefile)));bindings[str(scorefile)]=sha(scorefile);print('FULL_RESOURCE_HISTORY_GATE',case,passed,json.dumps({k:(v['spearman'],v['top_k_hits']) for k,v in results['BH'].items()}),flush=True)
 assert len(rows)==9 and sha(frozen)==frozen_hash and all(sha(p)==h for p,h in bindings.items());(D/'models.json').write_text(json.dumps(dict(folds=folds),indent=2)+'\n');(D/'verification.json').write_text(json.dumps(encode(dict(status='GROUP_HELDOUT_FULL_DOMAIN_HISTORY_FORECAST_SCORED',rows=rows,passed_available_cases=sum(x['pass_both_controls'] for x in rows),available_cases=6,required_cases=9,full9_gate=False,bindings=bindings,frozen_features_sha256=frozen_hash,models_sha256=sha(D/'models.json'),offline_study_seconds=time.perf_counter()-tick,scope='Exposed development, no native intervention/unseen/fullpaid/hardware claim.')),indent=2)+'\n')
if __name__=='__main__':main()
