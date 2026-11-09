"""Separate target-only namespace, joined to frozen label-free feature IDs."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]


def main():
    out=R/'experiments/mmc_coupled_ridge_labels_v1_2026-10-19';out.mkdir(exist_ok=False)
    source=R/'experiments/mmc_complete_NET_choice_diagnostic_v1_2026-10-19';rp=source/'results.json';vp=source/'independent_verification_v1.json';d=json.loads(rp.read_text());v=json.loads(vp.read_text());assert v['status']=='ALL3_COMPLETE_NET_CHOICES_LEDGER_OVERFLOW_SIX_METRICS_AND_COMPARISONS_VERIFIED' and v['bindings'][str(rp)]==sha(rp)
    protocol=R/'experiments/mmc_coupled_ridge_development_protocol_v1_2026-10-19/protocol.json';plan=json.loads(protocol.read_text());bindings={str(p):sha(p) for p in [rp,vp,protocol,Path(__file__).resolve()]};rows=[]
    for fold in plan['folds']:
        case=fold['evaluation_case'];choices=source/case/'choices.jsonl';assert d['bindings'][str(choices)]==sha(choices);features=R/'experiments/mmc_label_free_NET_features_v1_2026-10-19'/(case+'.jsonl');assert plan['bindings'][str(features)]==sha(features);ids={x['net_id'] for x in map(json.loads,features.open())};seen=set();total=0;counts={'positive':0,'zero':0,'negative':0};target=out/(case+'.jsonl')
        with target.open('x') as f:
            for x in map(json.loads,choices.open()):
                net=x['net_id'];assert net not in seen and net in ids;seen.add(net);a,b=x['A_error'],x['B_error'];assert type(a) is type(b) is int and min(a,b)>=0;y=a-b;total+=y;counts['positive' if y>0 else 'negative' if y<0 else 'zero']+=1;f.write(json.dumps(dict(net_id=net,y=y),separators=(',',':'))+'\n')
        assert seen==ids and len(ids)==55300;ref=next(x for x in d['cases'] if x['case']==case)['per_NET_CHANNEL_errors'];assert total==ref['A']-ref['B']
        bindings.update({str(p):sha(p) for p in [choices,features,target]});rows.append(dict(case=case,NETs=len(ids),sum_target=total,counts=counts));print('RIDGE_LABEL_NAMESPACE_BUILT',case,counts,flush=True)
    (out/'verification.json').write_text(json.dumps(dict(status='ALL3_TARGET_ONLY_LABEL_TABLES_MATCH_FROZEN_AUDITED_NET_ERRORS_AND_FEATURE_IDS',rows=rows,bindings=bindings,scope='Target-only training/evaluation namespace, derived from previously independently verified perNET native-union errors. Never inference input. PerNET loss surrogate is not a bound on global rank/MAE.'),indent=2)+'\n')


if __name__=='__main__':main()
