"""Frozen whole-episode exposure ablations and exact probability ranking."""
import json
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]
D=R/'experiments/prince_paired_exposure_features_v1_2026-10-20'
S=R/'experiments/prince_paired_cost_state_v1_2026-10-20'

def load(p):return json.loads(p.read_text())
def feature(r,name):
    fields={'pooled':[], 'stock':['occupancy','acc_bits'],
            'stockE':['occupancy','acc_bits','E'],
            'stockQ':['occupancy','acc_bits','Q'],
            'stockEQ':['occupancy','acc_bits','E','Q']}[name]
    return tuple(r[k] for k in fields)

def main():
    frozen=load(D/'frozen_features.json')
    for p,h in frozen['bindings'].items():assert sha(p)==h
    names=load(D/'protocol.json')['candidates']
    requests=load(S/'frozen_inputs.json')['requests']
    targets={(r['case'],r['mode'],r['horizon']):r for r in load(S/'dataset_manifest.json')['rows']}
    features={r['case']:{a['id']:a for a in map(json.loads,Path(r['features']).open())}
              for r in frozen['rows'] if r['status']=='READY_ONLY_FEATURES_FROZEN'}
    data={}
    for i,q in enumerate(requests):
        if q['status']!='READY_PLAN_FROZEN':continue
        row=targets[q['case'],q['mode'],q['horizon']]
        assert sha(row['target_file'])==row['target_sha256']
        data[i]={t['id']:t['occupancy'] for t in map(json.loads,Path(row['target_file']).open())}
        assert set(data[i])==set(features[q['case']])
    results=[];models=[]
    for fold in load(S/'grouped_folds.json')['folds']:
        tables={name:defaultdict(Counter) for name in names}
        for i in fold['train_requests']:
            q=requests[i];context=(q['mode'],q['horizon'])
            for node,truth in data[i].items():
                r=features[q['case']][node]
                for name in names:tables[name][context+feature(r,name)][truth]+=1
        moments={name:{k:(sum(c.values()),sum(o*v for o,v in c.items()),
                          sum(v for o,v in c.items() if o>0),sum(max(o-1,0)*v for o,v in c.items()),
                          sum(v for o,v in c.items() if o>1)) for k,c in table.items()}
                 for name,table in tables.items()}
        models.append(dict(heldout_episode=fold['heldout_episode'],train_requests=fold['train_requests'],
                           tables={name:[dict(key=list(k),counts=dict(c)) for k,c in table.items()] for name,table in tables.items()}))
        for i in fold['test_requests']:
            q=requests[i];context=(q['mode'],q['horizon']);truth=data[i];n=len(truth);K=max(1,n//20)
            for name in names+['train_prevalence','zero_event']:
                scores=[];errors=[0.,0.,0.,0.];prediction=0.;fallback=0
                for node,t in truth.items():
                    r=features[q['case']][node];occ=r['occupancy'];base=moments['pooled'][context]
                    if name=='zero_event':
                        prob=Fraction(0);mu,pos,ex=0.,0.,0.
                    elif name=='train_prevalence':
                        count,total,positive,excess,hits=base
                        prob=Fraction(hits,count);mu=total/count;pos=positive/count;ex=excess/count
                    else:
                        key=context+feature(r,name)
                        fallback+=key not in moments[name]
                        count,total,positive,excess,hits=moments[name].get(key,base)
                        prob=Fraction(hits+int(occ>1),count+1)
                        mu=(total+occ)/(count+1);pos=(positive+int(occ>0))/(count+1);ex=(excess+max(occ-1,0))/(count+1)
                    errors[0]+=(float(prob)-int(t>1))**2
                    errors[1]+=(mu-t)**2;errors[2]+=(pos-int(t>0))**2;errors[3]+=(ex-max(t-1,0))**2
                    prediction+=float(prob);scores.append((prob,node))
                selected=[node for prob,node in sorted(scores,key=lambda a:(-a[0],a[1]))[:K]]
                hits=sum(truth[node]>1 for node in selected);events=sum(t>1 for t in truth.values())
                results.append(dict(case=q['case'],mode=q['mode'],horizon=q['horizon'],model=name,
                    heldout_episode=fold['heldout_episode'],resources=n,event_rows=events,event_Brier=errors[0]/n,
                    occupancy_MSE=errors[1]/n,positive_Brier=errors[2]/n,excess_MSE=errors[3]/n,
                    predicted_event_total=prediction,topK=K,topK_hits=hits,topK_precision=hits/K,
                    topK_recall=hits/events if events else None,selected_resource_ids=selected,pooled_fallback_resources=fallback))
    assert len(results)==336
    out=dict(status='EXPOSURE_ABLATIONS_SCORED_PENDING_INDEPENDENT_AUDIT',scores=results,models=models,
             original_full9_gate=False,unavailable_requests=24,
             reference_scope='zero_event other target moments set0 solely as diagnostic;not a routing forecast. Exact Fraction probability ordering,ascendingID ties,floor(N/20).',
             bindings={str(p):sha(p) for p in [D/'protocol.json',D/'frozen_features.json',D/'independent_feature_verification_v1.json',S/'dataset_manifest.json',S/'grouped_folds.json',Path(__file__)]})
    with (D/'evaluation_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    for name in names+['train_prevalence','zero_event']:
        rows=[r for r in results if r['model']==name];total=sum(r['resources'] for r in rows)
        print(name,'eventBrier',sum(r['event_Brier']*r['resources'] for r in rows)/total,
              'topK_hits',sum(r['topK_hits'] for r in rows),'/',sum(r['event_rows'] for r in rows),flush=True)

if __name__=='__main__':main()
