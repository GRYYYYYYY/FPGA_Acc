"""Positive-mass-preserving tail projection, using frozen nested weights."""
import json
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
D=R/'experiments/prince_paired_exposure_features_v1_2026-10-20'
S=R/'experiments/prince_paired_cost_state_v1_2026-10-20'
def load(p):return json.loads(p.read_text())
def main():
    audit=load(D/'nested_shrinkage_independent_verification_v1.json')
    for p,h in audit['bindings'].items():assert sha(p)==h
    old=load(D/'evaluation_v1.json');nested=load(D/'nested_shrinkage_evaluation_v1.json')
    features={r['case']:{a['id']:a for a in map(json.loads,Path(r['features']).open())} for r in load(D/'frozen_features.json')['rows'] if r['status']=='READY_ONLY_FEATURES_FROZEN'}
    weights={r['heldout_episode']:F.from_float(r['weight']) for r in nested['fits']}
    models={}
    for m in old['models']:
        models[m['heldout_episode']]={kind:{tuple(r['key']):{int(k):v for k,v in r['counts'].items()} for r in m['tables'][kind]} for kind in ['pooled','stockQ']}
    scores=[];certificates=[]
    for row in load(S/'dataset_manifest.json')['rows']:
        if row['status']=='NO_READY_INPUT_UNAVAILABLE':continue
        episode=row['case'].split('/')[1];model=models[episode];w=weights[episode];context=row['mode'],row['horizon'];base=model['pooled'][context];nb=sum(base.values());truth={r['id']:r['occupancy'] for r in map(json.loads,Path(row['target_file']).open())};cache={};rank=[];errors=[0.,0.,0.,0.];clipped=0
        for node,t in truth.items():
            r=features[row['case']][node];key=context+(r['occupancy'],r['acc_bits'],r['Q'])
            if key not in cache:
                counts=dict(model['stockQ'].get(key,base));counts[r['occupancy']]=counts.get(r['occupancy'],0)+1;nq=sum(counts.values());support=set(base)|set(counts)
                s=F(sum(v for o,v in counts.items() if o>0),nq)
                tail={o:(1-w)*F(base.get(o,0),nb)+w*F(counts.get(o,0),nq) for o in support if o>1};total=sum(tail.values(),F(0));scale=min(F(1),s/total) if total else F(1)
                distribution={o:p*scale for o,p in tail.items()};distribution[0]=1-s;distribution[1]=s-scale*total
                assert all(p>=0 for p in distribution.values()) and sum(distribution.values())==1
                q=sum((p for o,p in distribution.items() if o>1),F(0));mu=sum((o*p for o,p in distribution.items()),F(0));ex=sum((max(o-1,0)*p for o,p in distribution.items()),F(0));assert mu==s+ex
                cache[key]=(q,float(mu),float(s),float(ex),scale<1)
                certificates.append(dict(case=row['case'],mode=row['mode'],horizon=row['horizon'],key=list(key),distribution={str(o):[p.numerator,p.denominator] for o,p in distribution.items()}))
            q,mu,s,ex,c=cache[key];clipped+=c;rank.append((q,node))
            for j,(p,y) in enumerate(zip([float(q),mu,s,ex],[int(t>1),t,int(t>0),max(t-1,0)])):errors[j]+=(p-y)**2
        n=len(truth);K=max(1,n//20);selected=[node for q,node in sorted(rank,key=lambda z:(-z[0],z[1]))[:K]];hits=sum(truth[node]>1 for node in selected)
        scores.append(dict(case=row['case'],mode=row['mode'],horizon=row['horizon'],resources=n,event_Brier=errors[0]/n,occupancy_MSE=errors[1]/n,positive_Brier=errors[2]/n,excess_MSE=errors[3]/n,topK=K,topK_hits=hits,event_rows=sum(t>1 for t in truth.values()),selected_resource_ids=selected,tail_scaled_resources=clipped))
        print('TAIL_FRAME',row['case'],row['mode'],row['horizon'],flush=True)
    out=dict(status='TAIL_PROJECTED_DISTRIBUTIONS_SCORED_PENDING_INDEPENDENT_AUDIT',scores=scores,distributions=certificates,original_full9_gate=False,bindings={str(p):sha(p) for p in [D/'tail_projection_design_v1.json',D/'nested_shrinkage_evaluation_v1.json',D/'nested_shrinkage_independent_verification_v1.json',D/'evaluation_v1.json',D/'frozen_features.json',S/'dataset_manifest.json',Path(__file__)]})
    with (D/'tail_projection_evaluation_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    n=sum(s['resources'] for s in scores)
    print({k:sum(s[k]*s['resources'] for s in scores)/n for k in ['event_Brier','occupancy_MSE','positive_Brier','excess_MSE']})
    print('TOPK_HITS',sum(s['topK_hits'] for s in scores))
if __name__=='__main__':main()
