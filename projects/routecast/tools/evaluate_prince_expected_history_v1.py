"""Finite-support exact-additive history expectation, no future-input leakage."""
import json,struct
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict,Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments'
D=E/'prince_expected_history_v1_2026-10-20';S=E/'prince_paired_cost_state_v1_2026-10-20';X=E/'prince_paired_exposure_features_v1_2026-10-20'
def load(p):return json.loads(p.read_text())
def value(word):return struct.unpack('<f',int(word).to_bytes(4,'little'))[0]
def main():
    audit=load(X/'tail_projection_independent_verification_v1.json')
    for p,h in audit['bindings'].items():assert sha(p)==h
    tail=load(X/'tail_projection_evaluation_v1.json');distributions={(r['case'],r['mode'],r['horizon'],tuple(r['key'])):{int(o):F(*p) for o,p in r['distribution'].items()} for r in tail['distributions']}
    frozen=load(S/'frozen_inputs.json');requests={(r['case'],r['mode'],r['horizon']):r for r in frozen['requests']};features={r['case']:{a['id']:a for a in map(json.loads,Path(r['features']).open())} for r in load(X/'frozen_features.json')['rows'] if r['status']=='READY_ONLY_FEATURES_FROZEN'}
    models={}
    for fold in load(X/'evaluation_v1.json')['models']:
        models[fold['heldout_episode']]={tuple(r['key']):{int(o):v for o,v in r['counts'].items()} for r in fold['tables']['pooled']}
    scores=[];certs=[];checks=0
    for row in load(S/'dataset_manifest.json')['rows']:
        if row['status']=='NO_READY_INPUT_UNAVAILABLE':continue
        case,mode,h=row['case'],row['mode'],row['horizon'];q=requests[case,mode,h];alphas=[value(w) for w in q['planned_alpha_after_search_bits']];assert all(a in [0,1] for a in alphas)
        groups=defaultdict(Counter)
        for target in map(json.loads,Path(row['target_file']).open()):
            r=features[case][target['id']];ready=value(r['acc_bits']);actual=value(target['acc_after_global_bits']);assert ready==int(ready) and actual==int(actual) and 0<=ready<=actual<2**24
            key=r['occupancy'],r['acc_bits'],r['Q'];groups[key][int(actual-ready)]+=1;checks+=1
        errors={m:F(0) for m in ['persistence','pooled','tail']};bias={m:F(0) for m in errors};n=0
        for key,hist in groups.items():
            delta=pooled=F(0);maximum=0;ready=int(value(key[1]))
            for j,alpha in enumerate(alphas,1):
                dist=distributions[case,mode,j,(mode,j)+key];assert sum(dist.values())==1
                delta+=int(alpha)*sum((max(o-1,0)*p for o,p in dist.items()),F(0));maximum+=int(alpha)*max(max(o-1,0) for o in dist)
                c=models[case.split('/')[1]][mode,j];pooled+=int(alpha)*F(sum(max(o-1,0)*v for o,v in c.items()),sum(c.values()))
            assert ready+maximum<2**24
            estimates=dict(persistence=F(0),pooled=pooled,tail=delta)
            certs.append(dict(case=case,mode=mode,horizon=h,key=list(key),target_increment_histogram=dict(hist),predicted_increment={m:[v.numerator,v.denominator] for m,v in estimates.items()},support_max_increment=maximum))
            for t,count in hist.items():
                n+=count
                for m,p in estimates.items():errors[m]+=count*(p-t)**2;bias[m]+=count*(p-t)
        scores.append(dict(case=case,mode=mode,horizon=h,resources=n,history_held=all(a==0 for a in alphas),metrics={m:dict(MSE=float(e/n),aggregate_bias=float(bias[m])) for m,e in errors.items()}))
    out=dict(status='FINITE_SUPPORT_EXPECTED_HISTORY_SCORED_PENDING_INDEPENDENT_AUDIT',rows=scores,groups=certs,resource_rows=checks,original_full9_gate=False,bindings={str(p):sha(p) for p in [D/'protocol.json',X/'tail_projection_evaluation_v1.json',X/'tail_projection_independent_verification_v1.json',S/'dataset_manifest.json',S/'frozen_inputs.json',Path(__file__)]})
    with (D/'evaluation_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    for m in ['persistence','pooled','tail']:
        a=[r for r in scores if not r['history_held']];n=sum(r['resources'] for r in a);print(m,sum(r['metrics'][m]['MSE']*r['resources'] for r in a)/n)
    print('EXACT_ADDITIVE_RESOURCE_ROWS',checks)
if __name__=='__main__':main()
