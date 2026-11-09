"""Independent count reconstruction and cross-multiplied topK certificates."""
import json,math
from pathlib import Path
from collections import Counter,defaultdict
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/prince_paired_exposure_features_v1_2026-10-20';S=R/'experiments/prince_paired_cost_state_v1_2026-10-20'
def load(p):return json.loads(p.read_text())
def fields(r,name):
 a=() if name=='pooled' else (r['occupancy'],r['acc_bits'])
 if name in ['stockE','stockEQ']:a+=(r['E'],)
 if name in ['stockQ','stockEQ']:a+=(r['Q'],)
 return a

def main():
 x=load(D/'evaluation_v1.json')
 for p,h in x['bindings'].items():assert sha(p)==h
 requests=load(S/'frozen_inputs.json')['requests'];targets={(r['case'],r['mode'],r['horizon']):r for r in load(S/'dataset_manifest.json')['rows']};features={r['case']:{a['id']:a for a in map(json.loads,Path(r['features']).open())} for r in load(D/'frozen_features.json')['rows'] if r['status']=='READY_ONLY_FEATURES_FROZEN'};data={}
 for i,q in enumerate(requests):
  if q['status']=='READY_PLAN_FROZEN':data[i]={a['id']:a['occupancy'] for a in map(json.loads,Path(targets[q['case'],q['mode'],q['horizon']]['target_file']).open())}
 checked=rankchecks=0
 for fold in load(S/'grouped_folds.json')['folds']:
  stored=next(m for m in x['models'] if m['heldout_episode']==fold['heldout_episode']);assert stored['train_requests']==fold['train_requests'];tables={}
  for name,entries in stored['tables'].items():
   actual=defaultdict(Counter)
   for i in fold['train_requests']:
    q=requests[i]
    for node,t in data[i].items():actual[(q['mode'],q['horizon'])+fields(features[q['case']][node],name)][t]+=1
   saved={tuple(r['key']):Counter({int(k):v for k,v in r['counts'].items()}) for r in entries};assert dict(actual)==saved
   tables[name]={k:(sum(c.values()),sum(t*v for t,v in c.items()),sum(v for t,v in c.items() if t>0),sum(max(t-1,0)*v for t,v in c.items()),sum(v for t,v in c.items() if t>1)) for k,c in actual.items()}
  for score in [s for s in x['scores'] if s['heldout_episode']==fold['heldout_episode']]:
   q=score;truth=data[next(i for i in fold['test_requests'] if (requests[i]['case'],requests[i]['mode'],requests[i]['horizon'])==(q['case'],q['mode'],q['horizon']))];name=q['model'];context=q['mode'],q['horizon'];base=tables['pooled'][context];probs={};sums=[0.,0.,0.,0.];prediction=0.;fallback=0
   for node,t in truth.items():
    r=features[q['case']][node];o=r['occupancy']
    if name=='zero_event':a,b=0,1;mu,pos,ex=0.,0.,0.
    elif name=='train_prevalence':
     n,total,positive,excess,hits=base;a,b=hits,n;mu,pos,ex=total/n,positive/n,excess/n
    else:
     key=context+fields(r,name);fallback+=key not in tables[name];n,total,positive,excess,hits=tables[name].get(key,base);a,b=hits+(o>1),n+1;mu,pos,ex=(total+o)/b,(positive+(o>0))/b,(excess+max(o-1,0))/b
    probs[node]=(a,b);p=a/b;prediction+=p
    for j,error in enumerate([(p-(t>1))**2,(mu-t)**2,(pos-(t>0))**2,(ex-max(t-1,0))**2]):sums[j]+=error
   N=len(truth)
   for j,metric in enumerate(['event_Brier','occupancy_MSE','positive_Brier','excess_MSE']):assert math.isclose(sums[j]/N,score[metric],abs_tol=1e-12,rel_tol=1e-12)
   assert math.isclose(prediction,score['predicted_event_total'],abs_tol=1e-8);assert fallback==score['pooled_fallback_resources']
   chosen=score['selected_resource_ids'];assert len(chosen)==len(set(chosen))==max(1,N//20)==score['topK']
   def precedes(left,right):
    a,b=probs[left];c,d=probs[right];return a*d>c*b or (a*d==c*b and left<right)
   assert all(precedes(a,b) for a,b in zip(chosen,chosen[1:]));selected=set(chosen);last=chosen[-1]
   for node in truth:
    if node not in selected:assert precedes(last,node);rankchecks+=1
   hits=sum(truth[n]>1 for n in chosen);events=sum(t>1 for t in truth.values());assert hits==score['topK_hits'] and events==score['event_rows'];assert math.isclose(hits/len(chosen),score['topK_precision']);assert math.isclose(hits/events,score['topK_recall']);checked+=1
 out=dict(status='ALL336_SCORES_TRAIN_COUNTS_AND_EXACT_TOPK_BOUNDARIES_RECONCILED',score_rows=checked,excluded_resource_rank_checks=rankchecks,scope='Independent training counts,moment scoring and integer cross-product ranking;whole-episode development only.',bindings={str(p):sha(p) for p in [D/'evaluation_v1.json',Path(__file__)]})
 with (D/'independent_prediction_verification_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print(out['status'],rankchecks)
if __name__=='__main__':main()
