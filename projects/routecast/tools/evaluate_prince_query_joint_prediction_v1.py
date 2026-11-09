"""Known-history-centered joint-moment prediction, whole-episode heldout."""
import json,struct
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_query_joint_prediction_v1_2026-10-20';S=E/'prince_future_query_joint_v1_2026-10-20'
def load(p):return json.loads(p.read_text())
def number(w):return int(struct.unpack('<f',int(w).to_bytes(4,'little'))[0])
def main():
    protocol=load(D/'protocol.json')
    for p,h in protocol['bindings'].items():assert sha(p)==h
    manifest=load(S/'dataset_manifest.json');data={};ready={}
    for row in manifest['rows']:
        if row['status']!='FUTURE_QUERY_LABELS_EXTRACTED':continue
        case=row['case'];ready[case]={r['id']:r for r in map(json.loads,Path(row['ready_feature_file']).open())};data[case,row['horizon']]=list(map(json.loads,Path(row['target_file']).open()))
    def key(r):return r['occupancy'],r['acc_bits'],r['Q']
    fits=[];scores=[];predictions=[]
    for episode in ['episode_01','episode_02','episode_03']:
        train=sorted(c for c in ready if c.split('/')[1]!=episode);test=sorted(set(ready)-set(train));assert len(train)==4 and len(test)==2;pool=defaultdict(lambda:[0,0,0,0]);cells=defaultdict(lambda:[0,0,0,0])
        for case in train:
            for h in [1,2]:
                for r in data[case,h]:
                    if not r['calls']:continue
                    feature=ready[case][r['id']];a=number(feature['acc_bits']);m=r['moment_sums'];n=r['calls'];delta=m['A']-a*n;df=m['A_F_other']-a*m['F_other'];assert delta>=0 and df>=0
                    if h==1:assert delta==df==0
                    values=[n,delta,m['F_other'],df]
                    for table,k in [(pool,(h,)),(cells,(h,)+key(feature))]:
                        for j,v in enumerate(values):table[k][j]+=v
        fits.append(dict(heldout_episode=episode,train_cases=train,test_cases=test,pooled=[dict(key=list(k),sums=v) for k,v in pool.items()],cells=[dict(key=list(k),sums=v) for k,v in cells.items()]))
        for case in test:
            for h in [1,2]:
                loss={m:F(0) for m in ['joint','product','known_history']};node_loss=dict(loss);calls=queried=missing=fallback=0
                for r in data[case,h]:
                    feature=ready[case][r['id']];k=(h,)+key(feature);fallback+=k not in cells;n,d,f,df=cells.get(k,pool[h,]);a=number(feature['acc_bits']);delta=F(d,n);other=F(f,n);joint=F(df,n);p=dict(joint=a*other+joint,product=(a+delta)*other,known_history=a*other)
                    if h==1:assert len(set(p.values()))==1
                    predictions.append(dict(case=case,horizon=h,id=r['id'],observed_calls=r['calls'],predicted_AF={m:[v.numerator,v.denominator] for m,v in p.items()}))
                    if not r['calls']:missing+=1;continue
                    queried+=1;calls+=r['calls'];truth=F(r['moment_sums']['A_F_other'],r['calls']);second=0
                    for entry in r['joint']:second+=(number(entry['acc_bits'])*entry['F_other'])**2*entry['calls']
                    for m,v in p.items():loss[m]+=second-2*v*r['moment_sums']['A_F_other']+r['calls']*v*v;node_loss[m]+=(v-truth)**2
                scores.append(dict(case=case,horizon=h,calls=calls,queried_resources=queried,no_query_resources=missing,pooled_fallback_resources=fallback,metrics={m:dict(call_MSE=float(loss[m]/calls),queried_resource_mean_MSE=float(node_loss[m]/queried)) for m in loss}))
        print('JOINT_FOLD',episode,flush=True)
    out=dict(status='RESIDUAL_JOINT_PREDICTION_SCORED_PENDING_AUDIT',fits=fits,scores=scores,predictions=predictions,unavailable_case_horizons=6,original_full9_gate=False,bindings={str(p):sha(p) for p in [D/'protocol.json',S/'dataset_manifest.json',S/'independent_verification_v1.json',Path(__file__)]})
    with (D/'evaluation_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    for h in [1,2]:
        rows=[r for r in scores if r['horizon']==h];total=sum(r['calls'] for r in rows)
        print(h,{m:sum(r['metrics'][m]['call_MSE']*r['calls'] for r in rows)/total for m in ['joint','product','known_history']})
if __name__=='__main__':main()
