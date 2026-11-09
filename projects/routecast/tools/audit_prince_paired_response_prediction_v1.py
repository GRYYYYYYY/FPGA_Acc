import json,hashlib,math
from pathlib import Path
from collections import Counter,defaultdict
D=Path.cwd()/'experiments/prince_paired_response_prediction_v1_2026-10-20';S=Path.cwd()/'experiments/prince_paired_cost_state_v1_2026-10-20'
def load(p):return json.loads(p.read_text())
x=load(D/'evaluation.json');requests=load(S/'frozen_inputs.json')['requests'];rows={(r['case'],r['mode'],r['horizon']):r for r in load(S/'dataset_manifest.json')['rows']};data={}
for i,q in enumerate(requests):
 if q['status']!='READY_PLAN_FROZEN':continue
 r=rows[q['case'],q['mode'],q['horizon']];ready={t['id']:t for t in map(json.loads,Path(r['input_file']).open())};data[i]=[(ready[t['id']]['occupancy'],ready[t['id']]['acc_bits'],t['occupancy']) for t in map(json.loads,Path(r['target_file']).open())]
checks=0
for fold in load(S/'grouped_folds.json')['folds']:
 model=next(m for m in x['models'] if m['heldout_episode']==fold['heldout_episode']);assert model['train_requests']==fold['train_requests'];pool=defaultdict(Counter);stock=defaultdict(Counter)
 for i in fold['train_requests']:
  q=requests[i];key=(q['mode'],q['horizon'])
  for o,a,t in data[i]:pool[key][t]+=1;stock[key+(o,a)][t]+=1
 for field,actual in [('pooled',pool),('stock',stock)]:assert {tuple(r['key']):Counter({int(k):v for k,v in r['counts'].items()}) for r in model[field]}==dict(actual)
 moments={}
 for name,table in [('policy_horizon_pooled',pool),('policy_horizon_stock',stock)]:
  for k,c in table.items():moments[name,k]=(sum(c.values()),sum(o*n for o,n in c.items()),sum(n for o,n in c.items() if o>0),sum((o-1)*n for o,n in c.items() if o>1))
 for i in fold['test_requests']:
  q=requests[i];k=(q['mode'],q['horizon'])
  for name in ['persistence','policy_horizon_pooled','policy_horizon_stock']:
   totals=[0.,0.,0.,0.];rare=0.;rn=0;fallback=0
   for o,a,t in data[i]:
    if name=='persistence':n,m,p,e=0,0,0,0
    elif name=='policy_horizon_stock' and k+(o,a) in stock:n,m,p,e=moments[name,k+(o,a)]
    else:
     n,m,p,e=moments['policy_horizon_pooled',k];fallback+=name=='policy_horizon_stock'
    mu=(m+o)/(n+1);pr=(p+(o!=0))/(n+1);ex=(e+max(o-1,0))/(n+1);truth=max(t-1,0)
    totals[0]+=(mu-t)**2;totals[1]+=(pr-(t!=0))**2;totals[2]+=(ex-truth)**2;totals[3]+=ex-truth
    if truth:rare+=(ex-truth)**2;rn+=1
   score=next(r for r in x['scores'] if (r['case'],r['mode'],r['horizon'],r['model'])==(q['case'],q['mode'],q['horizon'],name));N=len(data[i])
   for j,field in enumerate(['occupancy_MSE','positive_Brier','excess_MSE','aggregate_excess_bias']):assert math.isclose(score[field],totals[j]/N if j<3 else totals[j],rel_tol=1e-12,abs_tol=1e-12)
   assert score['excess_target_rows']==rn and score['pooled_fallback_resources']==fallback
   if rn:assert math.isclose(score['excess_target_only_MSE'],rare/rn,rel_tol=1e-12)
   checks+=1
out=dict(status='ALL144_SCORES_AND_WHOLE_EPISODE_TRAIN_COUNTS_INDEPENDENTLY_RECOMPUTED',score_rows=checks,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [D/'evaluation.json',Path(__file__)]},scope='Independent moment accumulator and source training-count reconstruction;development labels only,no original gate or native gain.')
with (D/'independent_verification_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(out['status'])
