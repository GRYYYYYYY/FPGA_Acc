"""Descriptive exact accounting of archived corrections, not a new predictor."""
import json
import math
from pathlib import Path
from fractions import Fraction
from collections import Counter
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]


def main():
    out=R/'experiments/mmc_wider_context_delta_direction_v1_2026-10-19'
    out.mkdir(exist_ok=False)
    bindings={str(Path(__file__).resolve()):sha(__file__)}
    rows=[]
    for family in ['owner_expansion','old_route_context','old_owner_pressure','source_context']:
        for i in range(1,4):
            case=f'case_{i:02d}'
            root=R/f'experiments/mmc_{family}_quality_v1_2026-10-18'/case
            vp,cp,pp,xp=[root/n for n in ['verification.json','comparison.json','protocol.json','vectors.json']]
            v,c,p,x=[json.loads(path.read_text()) for path in [vp,cp,pp,xp]]
            assert v['status']=='pass' and v['bindings'][str(cp)]==sha(cp)
            assert c['bindings'][str(xp)]==sha(xp) and c['bindings'][str(pp)]==sha(pp)
            candidate=p['primary_candidate']
            hist=Counter();counts=Counter();sums=Counter();ids=set()
            for item in x['channels']:
                assert item['node'] not in ids
                ids.add(item['node'])
                cap=Fraction(str(item['capacity']))
                old=Fraction(str(item['predictions']['previous_native']))/cap
                new=Fraction(str(item['predictions'][candidate]))/cap
                truth=Fraction(str(item['labels']['cold']))/cap
                hist[old,new,truth]+=1
                old_error,new_error=abs(old-truth),abs(new-truth)
                sums['old_error']+=old_error;sums['new_error']+=new_error
                if old==new:
                    counts['unchanged']+=1;sums['unchanged_error']+=old_error
                    continue
                counts['changed']+=1
                sums['changed_old_error']+=old_error;sums['changed_new_error']+=new_error
                delta=old_error-new_error
                if delta>0:counts['beneficial']+=1;sums['gross_improvement']+=delta
                elif delta<0:counts['harmful']+=1;sums['gross_harm']-=delta
                else:counts['neutral']+=1
                if old==truth:
                    counts['changed_previously_correct']+=1
                elif (new-old)*(truth-old)>0:
                    counts['toward_truth']+=1
                    if delta<0:counts['toward_truth_but_overshot_and_harmed']+=1
                else:counts['away_from_truth']+=1
            n=len(ids);assert n==258720 and len(x['channels'])==n
            # Separate joint-histogram accounting verifies every reported total.
            assert sums['old_error']==sum(k*abs(a-t) for (a,b,t),k in hist.items())
            assert sums['new_error']==sum(k*abs(b-t) for (a,b,t),k in hist.items())
            assert sums['gross_improvement']-sums['gross_harm']==sums['old_error']-sums['new_error']
            assert sums['unchanged_error']+sums['changed_new_error']==sums['new_error']
            assert counts['changed']==counts['beneficial']+counts['harmful']+counts['neutral']
            assert counts['changed']==counts['toward_truth']+counts['away_from_truth']+counts['changed_previously_correct']
            for name,key in [('previous_native','old_error'),(candidate,'new_error')]:
                assert math.isclose(float(sums[key]/n),float(c['metrics']['cold'][name]['concrete']['mae']),rel_tol=0,abs_tol=1e-12)
            rows.append(dict(family=family,case=case,candidate=candidate,counts=dict(counts),exact_error_sums={k:str(val) for k,val in sums.items()},
                unchanged_fraction_of_candidate_error=float(sums['unchanged_error']/sums['new_error']),
                net_MAE_improvement=float((sums['old_error']-sums['new_error'])/n)))
            bindings.update({str(path):sha(path) for path in [vp,cp,pp,xp]})
            print('DELTA_DIRECTION_ACCOUNTED',family,case,rows[-1]['net_MAE_improvement'],flush=True)
    with (out/'diagnosis.json').open('x') as f:
        json.dump(dict(status='TWELVE_ARCHIVED_CORRECTION_DIRECTION_AND_EXACT_ERROR_ACCOUNTINGS_PASS',rows=rows,bindings=bindings,
            scope='Retrospective exposed old case layouts, positive CHANNEL universe only. Exact row sums crosschecked by joint histogram and existing independently verified MAE. Not causal attribution, rank/topK bounds, independent route replay, heldout results or a prospective predictor. No model/parameter fitting.'),f,indent=2)


if __name__=='__main__':main()
