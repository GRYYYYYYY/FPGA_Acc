"""Frozen3fold development fits; each prediction uses feature-only heldout inputs."""
import json,time,math
from pathlib import Path
from collections import Counter
from coupled_NET_ridge_v1 import fit_fold,predict
from maximum_weight_NET_closure_v1 import solve,verify
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]


def write(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2)


def main():
    pp=R/'experiments/mmc_coupled_ridge_development_protocol_v1_2026-10-19/protocol.json';plan=json.loads(pp.read_text());out=R/'experiments/mmc_coupled_ridge_development_v1_2026-10-19';out.mkdir(exist_ok=False)
    features=R/'experiments/mmc_label_free_NET_features_v1_2026-10-19';labels=R/'experiments/mmc_coupled_ridge_labels_v1_2026-10-19';lp=labels/'verification.json';labelproof=json.loads(lp.read_text());fp=features/'independent_verification_v1.json';fv=json.loads(fp.read_text());assert fv['status']=='ALL3_165900_NETS_5142900_FEATURE_VALUES_AND_PINNED_INPUT_NAMESPACES_VERIFIED';assert labelproof['status']=='ALL3_TARGET_ONLY_LABEL_TABLES_MATCH_FROZEN_AUDITED_NET_ERRORS_AND_FEATURE_IDS'
    core=R/'experiments/coupled_NET_ridge_contract_v1_2026-10-19/verification.json';cv=json.loads(core.read_text());assert cv['status']=='RIDGE_CLOSED_FORM_CONSTANT_CORRELATED_COLUMNS_TRAIN_ONLY_SCALING_AND_HELDOUT_NONINTERFERENCE_PASS' and all(sha(p)==h for p,h in cv['bindings'].items())
    bindings={str(p):sha(p) for p in [pp,lp,fp,core,Path(__file__).resolve(),R/'tools/coupled_NET_ridge_v1.py',R/'tools/maximum_weight_NET_closure_v1.py']};source=R/'experiments/mmc_candidate_ownership_implications_v1_2026-10-19';inputplan=json.loads((R/'experiments/mmc_coupled_chooser_cost_and_data_scope_v1_2026-10-19/input_only_choice_protocol_v1.json').read_text());rows=[]
    def read_features(case):
        p=features/(case+'.jsonl');assert plan['bindings'][str(p)]==sha(p);bindings[str(p)]=sha(p);data={}
        for x in map(json.loads,p.open()):assert x['net_id'] not in data and len(x['values'])==31;data[x['net_id']]=x['values']
        assert len(data)==55300;return data
    for fold in plan['folds']:
        case=fold['evaluation_case'];directory=out/case;directory.mkdir();begin=time.perf_counter();training_features={};training_labels={};training_bindings={}
        for traincase in fold['training_cases']:
            assert traincase!=case;training_features[traincase]=read_features(traincase);p=labels/(traincase+'.jsonl');assert labelproof['bindings'][str(p)]==sha(p);training_labels[traincase]={x['net_id']:x['y'] for x in map(json.loads,p.open())};training_bindings.update({str(q):sha(q) for q in [features/(traincase+'.jsonl'),p]});bindings[str(p)]=sha(p)
        load_seconds=time.perf_counter()-begin;t=time.perf_counter();model=fit_fold(training_features,training_labels,fold['training_cases'],case);fit_seconds=time.perf_counter()-t;model['training_bindings']=training_bindings;model['feature_protocol_sha256']=sha(features/'protocol.json');write(directory/'model.json',model)
        # Evaluation feature table is opened only after fitting/serializing the
        # fold model. Its label file is never opened within this fold.
        del training_features,training_labels;t=time.perf_counter();test=read_features(case);gpath=source/case/'graph.json';bankpath=source/case/'banks.jsonl'
        for p in [gpath,bankpath]:assert inputplan['bindings'][str(p)]==sha(p);bindings[str(p)]=sha(p)
        g=json.loads(gpath.read_text());N=len(g['nodes']);assert set(test)==set(g['nodes']) and N==55300;weights={};predictions={}
        for net,x in test.items():
            value=predict(model,x);assert math.isfinite(value);q=round(10**6*value);predictions[net]=(value,q);weights[net]=(N+1)*q-1
        groups=g['components'];cw={i:sum(weights[n] for n in group) for i,group in enumerate(groups)};prediction_seconds=time.perf_counter()-t;t=time.perf_counter();cert=solve(cw,list(map(tuple,g['condensation_edges'])));verify(cw,list(map(tuple,g['condensation_edges'])),cert);solve_seconds=time.perf_counter()-t
        chosen={n for i in cert['selected'] for n in groups[i]};assert all(e['source'] not in chosen or e['target'] in chosen for e in g['edges']);ledger=Counter()
        for x in map(json.loads,bankpath.open()):ledger.update(x['B'] if x['net_id'] in chosen else x['A'])
        assert all(ledger[n]<=1 for n in g['eligible_resources'])
        cp=directory/'choices.jsonl'
        with cp.open('x') as f:
            for net in sorted(test):
                value,q=predictions[net];f.write(json.dumps(dict(net_id=net,predicted_gain=value,quantized_gain=q,encoded_weight=weights[net],pick='B' if net in chosen else 'A'),separators=(',',':'))+'\n')
        write(directory/'flow_cut_certificate.json',cert);write(directory/'ledger.json',dict(ledger));rows.append(dict(case=case,training_cases=fold['training_cases'],training_rows=model['training_rows'],evaluation_NETs=N,B_NETs=len(chosen),normal_equation_relative_residual=model['normal_equation_relative_residual'],training_load_seconds=load_seconds,fit_seconds=fit_seconds,prediction_seconds=prediction_seconds,solve_and_certificate_seconds=solve_seconds,case_component_seconds=time.perf_counter()-begin,heldout_label_file_opened_for_this_model=False,eligible_for_legal_route_commit=False))
        for p in [directory/'model.json',cp,directory/'flow_cut_certificate.json',directory/'ledger.json']:bindings[str(p)]=sha(p)
        print('COUPLED_RIDGE_FOLD_COMPLETE',case,'B',len(chosen),'fit_seconds',fit_seconds,flush=True)
    write(out/'receipt.json',dict(status='ALL3_FIXED_RIDGE_DEVELOPMENT_FITS_AND_CLOSED_CHOICES_PRODUCED',rows=rows,bindings=bindings,independent_verification_pending=True,scope=plan['scope'],quality_evaluation_executed=False))


if __name__=='__main__':main()
