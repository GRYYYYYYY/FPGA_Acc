"""Nested episode-only scalar mixture of whole occupancy distributions."""
import json
from collections import Counter, defaultdict
from pathlib import Path
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]
D=R/'experiments/prince_paired_exposure_features_v1_2026-10-20'
S=R/'experiments/prince_paired_cost_state_v1_2026-10-20'
def load(p):return json.loads(p.read_text())

def main():
    design=load(D/'nested_shrinkage_design_v1.json')
    old=load(D/'evaluation_v1.json')
    audit=load(D/'independent_prediction_verification_v1.json')
    for p,h in audit['bindings'].items():assert sha(p)==h
    requests=load(S/'frozen_inputs.json')['requests']
    targets={(r['case'],r['mode'],r['horizon']):r for r in load(S/'dataset_manifest.json')['rows']}
    features={r['case']:{a['id']:a for a in map(json.loads,Path(r['features']).open())}
              for r in load(D/'frozen_features.json')['rows'] if r['status']=='READY_ONLY_FEATURES_FROZEN'}
    data={}
    for i,q in enumerate(requests):
        if q['status']=='READY_PLAN_FROZEN':
            row=targets[q['case'],q['mode'],q['horizon']]
            assert sha(row['target_file'])==row['target_sha256']
            data[i]={t['id']:t['occupancy'] for t in map(json.loads,Path(row['target_file']).open())}
    def stock(r):return r['occupancy'],r['acc_bits'],r['Q']
    def fit(indices):
        pooled,local=defaultdict(Counter),defaultdict(Counter)
        for i in indices:
            q=requests[i];context=q['mode'],q['horizon']
            for node,t in data[i].items():
                pooled[context][t]+=1;local[context+stock(features[q['case']][node])][t]+=1
        def moments(c):
            return (sum(c.values()),sum(v for o,v in c.items() if o>1),sum(o*v for o,v in c.items()),
                    sum(v for o,v in c.items() if o>0),sum(max(o-1,0)*v for o,v in c.items()))
        return {k:moments(c) for k,c in pooled.items()},{k:moments(c) for k,c in local.items()}
    def predict(pooled,local,context,r):
        base=pooled[context];n=base[0];p0=tuple(v/n for v in base[1:])
        cell=local.get(context+stock(r),base);n=cell[0]+1;o=r['occupancy']
        prior=(int(o>1),o,int(o>0),max(o-1,0))
        pq=tuple((v+a)/n for v,a in zip(cell[1:],prior))
        return p0,pq
    scores=[];fits=[]
    for fold in load(S/'grouped_folds.json')['folds']:
        episodes=sorted({requests[i]['case'].split('/')[1] for i in fold['train_requests']})
        numerator=denominator=0.;inner=[]
        for episode in episodes:
            train=[i for i in fold['train_requests'] if requests[i]['case'].split('/')[1]!=episode]
            test=[i for i in fold['train_requests'] if requests[i]['case'].split('/')[1]==episode]
            pool,local=fit(train);groups=defaultdict(lambda:[0,0])
            for i in test:
                q=requests[i];context=q['mode'],q['horizon']
                for node,t in data[i].items():
                    r=features[q['case']][node];key=context+stock(r);groups[key][0]+=1;groups[key][1]+=t>1
            a=b=0.
            for key,(n,hits) in sorted(groups.items()):
                context=key[:2];r=dict(occupancy=key[2],acc_bits=key[3],Q=key[4]);p0,pq=predict(pool,local,context,r)
                delta=pq[0]-p0[0];a+=delta*(hits-n*p0[0]);b+=n*delta*delta
            numerator+=a;denominator+=b
            inner.append(dict(heldout_episode=episode,train_requests=train,test_requests=test,
                              numerator=a,denominator=b,validation_resources=sum(v[0] for v in groups.values())))
        weight=min(1.,max(0.,numerator/denominator)) if denominator else 0.
        fits.append(dict(heldout_episode=fold['heldout_episode'],weight=weight,numerator=numerator,denominator=denominator,inner=inner))
        pool,local=fit(fold['train_requests'])
        for i in fold['test_requests']:
            q=requests[i];context=q['mode'],q['horizon'];errors=[0.,0.,0.,0.];predicted=0.
            for node,t in data[i].items():
                p0,pq=predict(pool,local,context,features[q['case']][node])
                mixed=[a+weight*(b-a) for a,b in zip(p0,pq)]
                truths=[int(t>1),t,int(t>0),max(t-1,0)]
                assert abs(mixed[3]-(mixed[1]-mixed[2]))<1e-12
                for j,(p,y) in enumerate(zip(mixed,truths)):errors[j]+=(p-y)**2
                predicted+=mixed[0]
            n=len(data[i]);K=max(1,n//20)
            # A positive scalar mixture with a constant per-frame prevalence preserves exact ordering.
            previous=next(r for r in old['scores'] if (r['case'],r['mode'],r['horizon'],r['model'])==(q['case'],q['mode'],q['horizon'],'stockQ'))
            selected=previous['selected_resource_ids'] if weight>0 else sorted(data[i])[:K]
            hits=sum(data[i][node]>1 for node in selected);events=sum(t>1 for t in data[i].values())
            scores.append(dict(case=q['case'],mode=q['mode'],horizon=q['horizon'],resources=n,
                               event_Brier=errors[0]/n,occupancy_MSE=errors[1]/n,positive_Brier=errors[2]/n,excess_MSE=errors[3]/n,
                               predicted_event_total=predicted,event_rows=events,topK=K,topK_hits=hits,topK_recall=hits/events,
                               weight=weight,selected_resource_ids=selected))
        print('NESTED_WEIGHT',fold['heldout_episode'],weight,flush=True)
    out=dict(status='NESTED_TRAIN_ONLY_CALIBRATION_SCORED_PENDING_AUDIT',fits=fits,scores=scores,original_full9_gate=False,
             bindings={str(p):sha(p) for p in [D/'nested_shrinkage_design_v1.json',D/'evaluation_v1.json',D/'independent_prediction_verification_v1.json',D/'frozen_features.json',S/'dataset_manifest.json',S/'grouped_folds.json',Path(__file__)]})
    with (D/'nested_shrinkage_evaluation_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    total=sum(r['resources'] for r in scores)
    print('EVENT_BRIER',sum(r['resources']*r['event_Brier'] for r in scores)/total,'TOPK_HITS',sum(r['topK_hits'] for r in scores))

if __name__=='__main__':main()
