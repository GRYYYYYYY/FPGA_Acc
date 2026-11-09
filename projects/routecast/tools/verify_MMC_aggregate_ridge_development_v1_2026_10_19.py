"""Training-only statistics/gradient, heldout predictions and exact closed choices."""
import json,math,xml.parsers.expat as expat
from pathlib import Path
from array import array
from collections import Counter
from maximum_weight_NET_closure_v1 import verify
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]


def main():
    root=R/'experiments/mmc_aggregate_ridge_development_v1_2026-10-19';rp=root/'receipt.json';d=json.loads(rp.read_text());assert d['status']=='ALL3_AGGREGATE_TARGET_RIDGE_FITS_AND_CLOSED_CHOICES_PRODUCED' and all(sha(p)==h for p,h in d['bindings'].items())
    pp=R/'experiments/mmc_aggregate_ridge_development_protocol_v1_2026-10-19/protocol.json';plan=json.loads(pp.read_text());features=R/'experiments/mmc_label_free_NET_features_v1_2026-10-19';labels=R/'experiments/mmc_coupled_aggregate_labels_v1_2026-10-19';source=R/'experiments/mmc_candidate_ownership_implications_v1_2026-10-19';graph=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/rr/mmc/rr_graph.xml';caps=array('I');stack=[]
    class Done(Exception):pass
    def opening(tag,a):
        if tag=='node' and stack and stack[-1]=='rr_nodes':caps.append(int(a['capacity']))
        stack.append(tag)
    def closing(tag):
        assert stack.pop()==tag
        if tag=='rr_nodes':raise Done()
    parser=expat.ParserCreate();parser.StartElementHandler=opening;parser.EndElementHandler=closing
    try:
        with graph.open('rb') as f:
            for b in iter(lambda:f.read(1<<20),b''):parser.Parse(b,False)
    except Done:pass
    rows=[]
    def feature_table(case):return {x['net_id']:x['values'] for x in map(json.loads,(features/(case+'.jsonl')).open())}
    for fold in plan['folds']:
        case=fold['evaluation_case'];row=next(x for x in d['rows'] if x['case']==case);model=json.loads((root/case/'model.json').read_text());train=fold['training_cases'];assert model['training_cases']==sorted(train) and case not in train and model['evaluation_case']==case and model['alpha']==1
        expected_paths={str(p) for c in train for p in [features/(c+'.jsonl'),labels/(c+'.jsonl')]};assert set(model['training_bindings'])==expected_paths and all(sha(p)==h for p,h in model['training_bindings'].items());assert model['feature_protocol_sha256']==sha(features/'protocol.json')
        X=[];y=[]
        for c in sorted(train):
            f=feature_table(c);target={x['net_id']:x['y'] for x in map(json.loads,(labels/(c+'.jsonl')).open())};assert set(f)==set(target)
            for net in sorted(f):X.append(f[net]);y.append(target[net])
        assert len(X)==len(y)==model['training_rows']==110600
        for j in range(31):
            mean=math.fsum(x[j] for x in X)/len(X);scale=math.sqrt(math.fsum((x[j]-mean)**2 for x in X)/len(X)) or 1.
            assert mean==model['means'][j] and scale==model['scales'][j]
        assert math.fsum(y)/len(y)==model['target_mean'];means=model['means'];scales=model['scales'];beta=model['coefficients'];assert len(beta)==31
        residual=[]
        for x,target in zip(X,y):residual.append(model['target_mean']+sum(beta[j]*(x[j]-means[j])/scales[j] for j in range(31))-target)
        assert abs(math.fsum(residual))<1e-8*(1+math.fsum(abs(r) for r in residual))
        gradient=[]
        for j in range(31):
            terms=[(x[j]-means[j])/scales[j]*r for x,r in zip(X,residual)];value=math.fsum(terms)+beta[j];relative=abs(value)/(1+abs(beta[j])+math.fsum(abs(t) for t in terms));assert relative<1e-8;gradient.append(relative)
        del X,y,residual
        test=feature_table(case);choices={x['net_id']:x for x in map(json.loads,(root/case/'choices.jsonl').open())};assert set(choices)==set(test) and len(test)==55300;weights={};selected=set()
        for net,x in test.items():
            independent=model['target_mean']+sum(beta[j]*(x[j]-means[j])/scales[j] for j in range(31));choice=choices[net];value=choice['predicted_gain'];assert math.isclose(value,independent,rel_tol=1e-10,abs_tol=1e-10)
            assert choice['quantized_gain']==round(1e6*value);assert choice['encoded_weight']==55301*choice['quantized_gain']-1;weights[net]=choice['encoded_weight'];assert choice['pick'] in ['A','B']
            if choice['pick']=='B':selected.add(net)
        g=json.loads((source/case/'graph.json').read_text());groups=g['components'];cw={i:sum(weights[n] for n in c) for i,c in enumerate(groups)};certificate=json.loads((root/case/'flow_cut_certificate.json').read_text());objective=verify(cw,list(map(tuple,g['condensation_edges'])),certificate)
        assert selected=={n for i in certificate['selected'] for n in groups[i]} and all(e['source'] not in selected or e['target'] in selected for e in g['edges'])
        ledger=Counter();changes=0
        for bank in map(json.loads,(source/case/'banks.jsonl').open()):
            if bank['net_id'] in selected:ledger.update(bank['B']);changes+=int(bank['A']!=bank['B'])
            else:ledger.update(bank['A'])
        assert dict(ledger)=={int(n):v for n,v in json.loads((root/case/'ledger.json').read_text()).items()};assert all(ledger[n]<=1 for n in g['eligible_resources']) and len(selected)==row['B_NETs']
        rows.append(dict(case=case,training_rows=110600,evaluation_NETs=55300,actual_NET_ownership_changes=changes,B_selections=len(selected),full_overflow_units=sum(max(0,v-caps[n]) for n,v in ledger.items()),maximum_training_gradient_relative_residual=max(gradient),exact_encoded_objective=objective));print('RIDGE_TRAIN_STATS_GRADIENT_PREDICTIONS_FLOWCUT_LEDGER_PASS',case,'changed',changes,'overflow',rows[-1]['full_overflow_units'],flush=True)
    assert len(rows)==3
    with (root/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='ALL3_AGGREGATE_RIDGE_TRAIN_STATS_GRADIENTS_PREDICTIONS_FLOWCUT_LEDGER_PASS',rows=rows,bindings={str(p):sha(p) for p in [rp,pp,Path(__file__).resolve()]},scope='Separate source-data statistics and samplewise ridge gradient without refitting, independent prediction arithmetic and primal flow/cut certificate. Eval labels not read for each model; all old layouts exposed, not unseen-family validation.'),f,indent=2)


if __name__=='__main__':main()
