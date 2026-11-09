"""Independent rational distribution reconstruction and grouped score audit."""
import json,math
from fractions import Fraction as F
from pathlib import Path
from collections import defaultdict,Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/prince_paired_exposure_features_v1_2026-10-20';S=R/'experiments/prince_paired_cost_state_v1_2026-10-20'
def load(p):return json.loads(p.read_text())
def main():
 x=load(D/'tail_projection_evaluation_v1.json')
 for p,h in x['bindings'].items():assert sha(p)==h
 original=load(D/'evaluation_v1.json');models={}
 for m in original['models']:models[m['heldout_episode']]={kind:{tuple(r['key']):{int(k):v for k,v in r['counts'].items()} for r in m['tables'][kind]} for kind in ['pooled','stockQ']}
 weights={r['heldout_episode']:F.from_float(r['weight']) for r in load(D/'nested_shrinkage_evaluation_v1.json')['fits']};certs={};moments={}
 for r in x['distributions']:
  episode=r['case'].split('/')[1];key=tuple(r['key']);base=models[episode]['pooled'][key[:2]];local=dict(models[episode]['stockQ'].get(key,base));local[key[2]]=local.get(key[2],0)+1;n=sum(local.values());b=sum(base.values());w=weights[episode];s=1-F(local.get(0,0),n);tail={o:w*F(local.get(o,0),n)+(1-w)*F(base.get(o,0),b) for o in set(base)|set(local) if o>=2};T=sum(tail.values(),F(0));factor=s/T if T>s else F(1);expected={o:p*factor for o,p in tail.items()};expected[0]=1-s
  # p1 is positive mass minus the retained tail; compute directly to avoid a mass-correction convention.
  expected[1]=s-sum(p for o,p in expected.items() if o>=2)
  distribution={int(o):F(*p) for o,p in r['distribution'].items()};assert expected==distribution;assert sum(distribution.values())==1 and min(distribution.values())>=0
  q=sum(p for o,p in distribution.items() if o>=2);mu=sum(o*p for o,p in distribution.items());ex=sum((o-1)*p for o,p in distribution.items() if o>=2);assert mu==s+ex
  k=r['case'],r['mode'],r['horizon'],key;assert k not in certs;certs[k]=distribution;moments[k]=(q,float(mu),float(s),float(ex))
 features={r['case']:{a['id']:a for a in map(json.loads,Path(r['features']).open())} for r in load(D/'frozen_features.json')['rows'] if r['status']=='READY_ONLY_FEATURES_FROZEN'};targets={(r['case'],r['mode'],r['horizon']):r for r in load(S/'dataset_manifest.json')['rows']};checks=0;boundaries=0
 for score in x['scores']:
  case,mode,h=score['case'],score['mode'],score['horizon'];row=targets[case,mode,h];truth={r['id']:r['occupancy'] for r in map(json.loads,Path(row['target_file']).open())};hist=defaultdict(Counter);probs={}
  for node,t in truth.items():
   r=features[case][node];key=(mode,h,r['occupancy'],r['acc_bits'],r['Q']);k=case,mode,h,key;hist[k][t]+=1;probs[node]=moments[k][0]
  totals=[0.,0.,0.,0.]
  for k,c in hist.items():
   p=moments[k]
   for t,count in c.items():
    ys=[t>1,t,t>0,max(t-1,0)]
    for j in range(4):totals[j]+=count*(float(p[j])-ys[j])**2
  for j,name in enumerate(['event_Brier','occupancy_MSE','positive_Brier','excess_MSE']):assert math.isclose(totals[j]/len(truth),score[name],abs_tol=1e-12,rel_tol=1e-11)
  chosen=score['selected_resource_ids'];assert len(set(chosen))==len(chosen)==len(truth)//20
  def before(a,b):return probs[a]>probs[b] or (probs[a]==probs[b] and a<b)
  assert all(before(a,b) for a,b in zip(chosen,chosen[1:]));selected=set(chosen)
  for node in truth:
   if node not in selected:assert before(chosen[-1],node);boundaries+=1
  assert score['topK_hits']==sum(truth[n]>1 for n in chosen)
  old=next(s for s in original['scores'] if (s['case'],s['mode'],s['horizon'],s['model'])==(case,mode,h,'stockQ'));assert math.isclose(old['positive_Brier'],score['positive_Brier'],abs_tol=1e-12);checks+=1
 out=dict(status='ALL_TAIL_DISTRIBUTIONS_AND48_SCORES_INDEPENDENTLY_RECONCILED',distributions=len(certs),score_rows=checks,excluded_rank_checks=boundaries,scope='Independent rational tail reconstruction,positive-mass invariance,grouped scoring and exact ranking boundaries;no original quality/native admission.',bindings={str(p):sha(p) for p in [D/'tail_projection_evaluation_v1.json',Path(__file__)]})
 with (D/'tail_projection_independent_verification_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print(out['status'])
if __name__=='__main__':main()
