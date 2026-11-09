"""Independent exact inner regression and grouped outer-score verification."""
import json,math
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction as F
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/prince_paired_exposure_features_v1_2026-10-20';S=R/'experiments/prince_paired_cost_state_v1_2026-10-20'
def load(p):return json.loads(p.read_text())
def main():
 x=load(D/'nested_shrinkage_evaluation_v1.json')
 for p,h in x['bindings'].items():assert sha(p)==h
 req=load(S/'frozen_inputs.json')['requests'];labels={(r['case'],r['mode'],r['horizon']):r for r in load(S/'dataset_manifest.json')['rows']};features={r['case']:{a['id']:a for a in map(json.loads,Path(r['features']).open())} for r in load(D/'frozen_features.json')['rows'] if r['status']=='READY_ONLY_FEATURES_FROZEN'};groups={};node_truth={}
 for i,q in enumerate(req):
  if q['status']!='READY_PLAN_FROZEN':continue
  grouped=defaultdict(Counter);truth={}
  for t in map(json.loads,Path(labels[q['case'],q['mode'],q['horizon']]['target_file']).open()):
   r=features[q['case']][t['id']];key=q['mode'],q['horizon'],r['occupancy'],r['acc_bits'],r['Q'];grouped[key][t['occupancy']]+=1;truth[t['id']]=t['occupancy']
  groups[i]=grouped;node_truth[i]=truth
 def fit(indices):
  a,b=defaultdict(Counter),defaultdict(Counter)
  for i in indices:
   for key,c in groups[i].items():a[key[:2]].update(c);b[key].update(c)
  return a,b
 def predictions(a,b,key):
  base=a[key[:2]];local=b.get(key,base);o=key[2];n=sum(base.values());m=sum(local.values())+1
  funcs=[lambda t:int(t>1),lambda t:t,lambda t:int(t>0),lambda t:max(t-1,0)]
  return ([F(sum(f(t)*v for t,v in base.items()),n) for f in funcs],
          [F(sum(f(t)*v for t,v in local.items())+f(o),m) for f in funcs])
 checks=0;weightcerts=[]
 for fold in load(S/'grouped_folds.json')['folds']:
  fitted=next(f for f in x['fits'] if f['heldout_episode']==fold['heldout_episode']);num=F(0);den=F(0)
  for inner in fitted['inner']:
   train=inner['train_requests'];test=inner['test_requests'];assert set(train).isdisjoint(test) and set(train)|set(test)==set(fold['train_requests'])
   assert all(req[i]['case'].split('/')[1]==inner['heldout_episode'] for i in test)
   assert all(req[i]['case'].split('/')[1]!=inner['heldout_episode'] for i in train)
   a,b=fit(train);u=v=F(0)
   for i in test:
    for key,c in groups[i].items():
     p,q=predictions(a,b,key);delta=q[0]-p[0];n=sum(c.values());hits=sum(v for t,v in c.items() if t>1);u+=delta*(hits-n*p[0]);v+=n*delta*delta
   assert math.isclose(float(u),inner['numerator'],abs_tol=1e-12);assert math.isclose(float(v),inner['denominator'],abs_tol=1e-12);num+=u;den+=v
  exact=max(F(0),min(F(1),num/den)) if den else F(0);assert math.isclose(float(exact),fitted['weight'],rel_tol=1e-12);weightcerts.append(dict(episode=fold['heldout_episode'],exact_weight=[exact.numerator,exact.denominator]))
  a,b=fit(fold['train_requests']);w=fitted['weight']
  for i in fold['test_requests']:
   q=req[i];score=next(s for s in x['scores'] if (s['case'],s['mode'],s['horizon'])==(q['case'],q['mode'],q['horizon']));errors=[0.,0.,0.,0.];pred=0.;N=0
   for key,c in groups[i].items():
    p,z=predictions(a,b,key);mix=[float(pj)+w*(float(zj)-float(pj)) for pj,zj in zip(p,z)];n=sum(c.values());N+=n;pred+=n*mix[0]
    for t,count in c.items():
     truth=[int(t>1),t,int(t>0),max(t-1,0)]
     for j in range(4):errors[j]+=count*(mix[j]-truth[j])**2
   for j,k in enumerate(['event_Brier','occupancy_MSE','positive_Brier','excess_MSE']):assert math.isclose(errors[j]/N,score[k],rel_tol=1e-11,abs_tol=1e-12)
   assert math.isclose(pred,score['predicted_event_total'],abs_tol=1e-8)
   old=next(s for s in load(D/'evaluation_v1.json')['scores'] if (s['case'],s['mode'],s['horizon'],s['model'])==(q['case'],q['mode'],q['horizon'],'stockQ'))
   assert w>0 and score['selected_resource_ids']==old['selected_resource_ids'];assert score['topK_hits']==sum(node_truth[i][n]>1 for n in score['selected_resource_ids']);checks+=1
 out=dict(status='ALL3_EXACT_INNER_WEIGHTS_AND48_OUTER_SCORES_RECONCILED',score_rows=checks,weights=weightcerts,scope='Exact rational inner training-only solution;independent grouped target histogram outer scores;positive scalar mixture preserves previously audited exact rankings.',bindings={str(p):sha(p) for p in [D/'nested_shrinkage_evaluation_v1.json',Path(__file__)]})
 with (D/'nested_shrinkage_independent_verification_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print(out['status'])
if __name__=='__main__':main()
