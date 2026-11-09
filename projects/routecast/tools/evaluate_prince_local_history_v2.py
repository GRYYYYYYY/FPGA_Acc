"""Single frozen local-history candidate and prespecified ablations; no search."""
import json,struct,time
from pathlib import Path
from fractions import Fraction
from collections import Counter
from pre_route_endpoints import sha
from expected_channel_forecast_vectors_v1 import vectors
from external_forecast_metrics_v1 import vectors as physical,metrics,gate
R=Path(__file__).resolve().parents[1];E=R/'experiments';S=E/'prince_local_history_v1_2026-10-20';D=E/'prince_local_history_evaluation_v2_2026-10-20'
def load(p):return json.loads(Path(p).read_text())
def word(x):return struct.unpack('<I',struct.pack('<f',float(x)))[0]
def value(w):return Fraction(struct.unpack('<f',struct.pack('<I',w))[0])
def paths(t,q):
 g='G';b=f'B/{t&1}';bp=f'BP/{t&3}';tt=f'T/{t}';return dict(BP=[bp,b,g],T=[tt,bp,b,g],BPQ=[f'BPQ/{t&3}/{q}',bp,b,g],TQ=[f'TQ/{t}/{q}',tt,bp,b,g])
def main():
 D.mkdir(exist_ok=False);tick=time.perf_counter();frozen=load(S/'frozen_features.json');assert all(sha(p)==h for p,h in frozen['bindings'].items());bindings={str(S/'frozen_features.json'):sha(S/'frozen_features.json'),str(Path(__file__)):sha(__file__)}
 for p in [R/'tools/expected_channel_forecast_vectors_v1.py',R/'tools/external_forecast_metrics_v1.py']:bindings[str(p)]=sha(p)
 data={};truths={};domains={};original={}
 for row in frozen['rows']:
  if row['status']!='FEATURES_FROZEN_NO_LABELS':continue
  c=row['case'];fp=Path(row['features']);data[c]=list(map(json.loads,fp.open()));sp=E/'prince_feedback_quality_v1_2026-10-20'/c/'specification.json';spec=load(sp);lp=Path(spec['label_physical_audit']);truths[c]={int(n):y for n,y in load(lp)['node_occupancy'].items()};assert all(truths[c].get(x['id'],0) in [0,1] for x in data[c]);folder=E/'prince_quality_domains_v1_2026-10-20'/c.split('/')[0];rp=folder/'resources.jsonl';bp=folder/'spatial_bins.json';mp=folder/'verification.json';domains[c]=(list(map(json.loads,rp.open())),load(bp),load(mp));cp=sp.parent/'comparison.json';original[c]=load(cp)
  for p in [fp,sp,lp,rp,bp,mp,cp]:bindings[str(p)]=sha(p)
 bycase={};folds=[];fit_tick=time.perf_counter()
 for ep in ['episode_01','episode_02','episode_03']:
  train=sorted(c for c in data if c.split('/')[1]!=ep);test=sorted(set(data)-set(train));assert len(train)==4 and len(test)==2;counts=Counter();positive=Counter()
  for c in train:
   for x in data[c]:
    keys=set(k for path in paths(x['T'],x['Q']).values() for k in path)
    for k in keys:counts[k]+=1;positive[k]+=truths[c].get(x['id'],0)
  cells={k:dict(resources=n,occupied=positive[k],word=word(Fraction(positive[k]+1,n+2))) for k,n in sorted(counts.items())};f=dict(heldout_episode=ep,train_cases=train,test_cases=test,cells=cells);folds.append(f)
  for c in test:bycase[c]=f
 fit_seconds=time.perf_counter()-fit_tick;modelp=D/'models.json'
 with modelp.open('x') as f:json.dump(dict(folds=folds,fit_seconds=fit_seconds),f,indent=2);f.write('\n')
 bindings[str(modelp)]=sha(modelp);rows=[];prior=load(E/'prince_temporal_stability_v1_2026-10-20/verification.json');prior={r['case']:r for r in prior['rows']};bindings[str(E/'prince_temporal_stability_v1_2026-10-20/verification.json')]=sha(E/'prince_temporal_stability_v1_2026-10-20/verification.json')
 for entry in frozen['rows']:
  c=entry['case']
  if c not in data:rows.append(dict(case=c,status=entry['status'],pass_both_controls=False));continue
  cells=bycase[c]['cells'];pred={name:{} for name in ['BP','T','BPQ','TQ']};scorep=D/c/'expected_counts.jsonl';scorep.parent.mkdir(parents=True);infer_tick=time.perf_counter()
  with scorep.open('x') as f:
   for x in data[c]:
    out=dict(id=x['id'])
    for name,path in paths(x['T'],x['Q']).items():
     key=next(k for k in path if k in cells);w=cells[key]['word'];out[name]=w;pred[name][x['id']]=value(w)
    f.write(json.dumps(out,separators=(',',':'))+'\n')
  inference_seconds=time.perf_counter()-infer_tick;resources,bins,meta=domains[c];truth=truths[c];labels=physical(resources,bins,truth,meta['graph_nodes'],truth=True);ms={name:metrics(vectors(resources,bins,p,meta['graph_nodes']),labels,meta['resource_k'],meta['spatial_k']) for name,p in pred.items()};checks={name:{ctrl:gate(m,original[c]['metrics'][ctrl]) for ctrl in ['previous_native','raw_min_on']} for name,m in ms.items()};assert json.loads(json.dumps(ms['BP'],default=lambda x:dict(numerator=x.numerator,denominator=x.denominator)))==prior[c]['metrics']['BP'];passed=all(x['pass_primary_gate'] for x in checks['TQ'].values());brier={name:float(sum((p[n]-truth.get(n,0))**2 for n in p)/len(p)) for name,p in pred.items()};rows.append(dict(case=c,status='SCORED',metrics=ms,checks=checks,pass_both_controls=passed,Brier=brier,score_file=str(scorep),inference_and_encoding_seconds=inference_seconds));bindings[str(scorep)]=sha(scorep);print('LOCAL_HISTORY_SCORED',c,passed,{name:dict(gate=all(x['pass_primary_gate'] for x in checks[name].values()),resource=(m['resource']['spearman'],m['resource']['top_k_hits']),spatial=(m['spatial']['spearman'],m['spatial']['top_k_hits']),Brier=brier[name]) for name,m in ms.items()},flush=True)
 assert all(sha(p)==h for p,h in bindings.items())
 with (D/'verification.json').open('x') as f:json.dump(dict(status='GROUP_HELDOUT_LOCAL_SHORT_HISTORY_SCORED',rows=rows,available_cases=6,required_cases=9,passed_available_cases=sum(r['pass_both_controls'] for r in rows),full9_gate=False,bindings=bindings,study_seconds=time.perf_counter()-tick,fit_seconds=fit_seconds,scope='Exposed development,independent audit pending. No native/fullpaid/unseen/hardware claim.'),f,indent=2,default=lambda x:dict(numerator=x.numerator,denominator=x.denominator));f.write('\n')
if __name__=='__main__':main()
