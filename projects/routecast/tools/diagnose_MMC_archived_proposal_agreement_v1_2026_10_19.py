"""Freeze prediction-only partitions, then diagnose each archived proposal."""
import json
from pathlib import Path
from fractions import Fraction
from collections import Counter, defaultdict
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]
FAMILIES=['owner_expansion','old_route_context','old_owner_pressure','source_context']
CLASSES=['all_unchanged','single_change','concordant_partial','unanimous_direction_different_value','unanimous_exact_change','opposing_directions']


def partition(old, values):
    signs=[(v>old)-(v<old) for v in values]
    active=[s for s in signs if s]
    if not active:return 0
    if len(active)==1:return 1
    if min(active)!=max(active):return 5
    if len(active)<4:return 2
    return 4 if len(set(values))==1 else 3


def main():
    out=R/'experiments/mmc_archived_proposal_agreement_v1_2026-10-19'
    out.mkdir(exist_ok=False)
    bindings={str(Path(__file__).resolve()):sha(__file__)}
    protocol=dict(families=FAMILIES,classes=CLASSES,
        rule='Compare each full archived candidate demand with previous_native per positive CHANNEL. Partition solely by four delta signs and exact value equality; no labels, learned weights or threshold selection in partition.',
        evaluation='Within each frozen partition measure each original candidate correction error versus previous_native. Do not synthesize mixed predictions or claim physical feasibility. Count unchanged candidates separately.',
        scope='Retrospective exposed case cohort. Shared inputs/algorithms make agreement correlated; no independent-vote probability, prospective quality or causal interpretation.')
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    rows=[]
    for i in range(1,4):
        case=f'case_{i:02d}';vectors=[];names=[]
        for family in FAMILIES:
            root=R/f'experiments/mmc_{family}_quality_v1_2026-10-18'/case
            paths=[root/n for n in ['verification.json','comparison.json','protocol.json','vectors.json']]
            verification,comparison,plan,vector=[json.loads(p.read_text()) for p in paths]
            assert verification['status']=='pass' and verification['bindings'][str(paths[1])]==sha(paths[1])
            assert comparison['bindings'][str(paths[3])]==sha(paths[3])
            vectors.append(vector['channels']);names.append(plan['primary_candidate'])
            bindings.update({str(p):sha(p) for p in paths})
        n=len(vectors[0]);assert n==258720 and all(len(x)==n for x in vectors)
        codes=bytearray();counts=Counter()
        for items in zip(*vectors):
            first=items[0]
            assert all((x['node'],x['capacity'],x['predictions']['previous_native'])==(first['node'],first['capacity'],first['predictions']['previous_native']) for x in items)
            old=first['predictions']['previous_native'];values=[x['predictions'][name] for x,name in zip(items,names)]
            code=partition(old,values);codes.append(code);counts[CLASSES[code]]+=1
        # Persist immutable prediction-only membership before any label accounting.
        cp=out/(case+'.classes.u8');cp.write_bytes(codes);bindings[str(cp)]=sha(cp)
        stats=defaultdict(Counter)
        for code,items in zip(codes,zip(*vectors)):
            truth=Fraction(str(items[0]['labels']['cold']))/Fraction(str(items[0]['capacity']))
            assert all(x['labels']['cold']==items[0]['labels']['cold'] for x in items)
            old=Fraction(str(items[0]['predictions']['previous_native']))/Fraction(str(items[0]['capacity']))
            for family,name,item in zip(FAMILIES,names,items):
                new=Fraction(str(item['predictions'][name]))/Fraction(str(item['capacity']))
                s=stats[CLASSES[code],family];s['resources']+=1
                s['old_error']+=abs(old-truth);s['candidate_error']+=abs(new-truth)
                if new==old:s['unchanged']+=1;continue
                s['changed']+=1;gain=abs(old-truth)-abs(new-truth)
                if gain>0:s['beneficial']+=1;s['gross_improvement']+=gain
                elif gain<0:s['harmful']+=1;s['gross_harm']-=gain
                else:s['neutral']+=1
                if old==truth:s['changed_previously_correct']+=1
        serialized=[]
        for (group,family),s in sorted(stats.items()):
            assert s['old_error']-s['candidate_error']==s['gross_improvement']-s['gross_harm']
            assert s['changed']==s['beneficial']+s['harmful']+s['neutral']
            serialized.append(dict(group=group,family=family,values={k:str(v) if isinstance(v,Fraction) else v for k,v in s.items()}))
        rows.append(dict(case=case,partition_counts=dict(counts),statistics=serialized))
        print('PROPOSAL_AGREEMENT_ACCOUNTED',case,dict(counts),flush=True)
    (out/'diagnosis.json').write_text(json.dumps(dict(status='ALL3_PREDICTION_ONLY_PARTITIONS_AND_CONDITIONAL_CORRECTION_ERRORS_ACCOUNTED',rows=rows,bindings=bindings,scope=protocol['scope']),indent=2)+'\n')


if __name__=='__main__':main()
