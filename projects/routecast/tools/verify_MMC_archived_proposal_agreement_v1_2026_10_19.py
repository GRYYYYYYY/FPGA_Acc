"""Independent order-comparison memberships and histogram conditional accounting."""
import json
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]


def main():
    root=R/'experiments/mmc_archived_proposal_agreement_v1_2026-10-19'
    result=root/'diagnosis.json';d=json.loads(result.read_text())
    assert all(sha(p)==h for p,h in d['bindings'].items())
    plan=json.loads((root/'protocol.json').read_text());families=plan['families'];classes=plan['classes']
    prior_path=R/'experiments/mmc_wider_context_delta_direction_v1_2026-10-19/diagnosis.json'
    prior=json.loads(prior_path.read_text());verified=[]
    for row in d['rows']:
        case=row['case'];vectors=[];names=[]
        for family in families:
            source=R/f'experiments/mmc_{family}_quality_v1_2026-10-18'/case
            vectors.append(json.loads((source/'vectors.json').read_text())['channels'])
            names.append(json.loads((source/'protocol.json').read_text())['primary_candidate'])
        codes=(root/(case+'.classes.u8')).read_bytes();assert len(codes)==258720
        histograms=defaultdict(Counter);counts=Counter()
        for code,items in zip(codes,zip(*vectors)):
            first=items[0];old=first['predictions']['previous_native']
            values=[x['predictions'][name] for x,name in zip(items,names)]
            above=sum(v>old for v in values);below=sum(v<old for v in values);changes=above+below
            if above and below:expected=5
            elif changes==0:expected=0
            elif changes==1:expected=1
            elif changes<4:expected=2
            elif max(values)==min(values):expected=4
            else:expected=3
            assert code==expected;counts[classes[code]]+=1
            for family,v in zip(families,values):histograms[classes[code],family][old,v,first['labels']['cold'],first['capacity']]+=1
        assert dict(counts)==row['partition_counts']
        totals=defaultdict(Counter)
        for stat in row['statistics']:
            key=stat['group'],stat['family'];s=Counter()
            for (a,b,t,cap),n in histograms[key].items():
                old=Fraction(str(a))/Fraction(str(cap));new=Fraction(str(b))/Fraction(str(cap));truth=Fraction(str(t))/Fraction(str(cap))
                e0,e1=abs(old-truth),abs(new-truth)
                s['resources']+=n;s['old_error']+=n*e0;s['candidate_error']+=n*e1
                if a==b:s['unchanged']+=n;continue
                s['changed']+=n
                if e0>e1:s['beneficial']+=n;s['gross_improvement']+=n*(e0-e1)
                elif e0<e1:s['harmful']+=n;s['gross_harm']+=n*(e1-e0)
                else:s['neutral']+=n
                if a==t:s['changed_previously_correct']+=n
            for k in set(s)|set(stat['values']):assert s[k]==Fraction(str(stat['values'].get(k,0))),(case,key,k)
            totals[stat['family']].update(s)
        for family,total in totals.items():
            old=next(x for x in prior['rows'] if x['case']==case and x['family']==family)
            assert total['old_error']==Fraction(old['exact_error_sums']['old_error'])
            assert total['candidate_error']==Fraction(old['exact_error_sums']['new_error'])
            for k in ['changed','beneficial','harmful','neutral','changed_previously_correct']:assert total[k]==old['counts'].get(k,0)
        verified.append(case);print('AGREEMENT_MEMBERSHIPS_HISTOGRAMS_AND_PRIOR_TOTALS_PASS',case,flush=True)
    assert len(verified)==3
    with (root/'independent_verification_v1.json').open('x') as f:
        json.dump(dict(status='ALL3_AGREEMENT_MEMBERSHIPS_HISTOGRAM_ERRORS_AND_TWELVE_PRIOR_TOTALS_VERIFIED',cases=verified,bindings={str(p):sha(p) for p in [result,prior_path,Path(__file__).resolve()]},scope='Independent arithmetic and membership verification, not a physical route audit or predictor quality test.'),f,indent=2)


if __name__=='__main__':main()
