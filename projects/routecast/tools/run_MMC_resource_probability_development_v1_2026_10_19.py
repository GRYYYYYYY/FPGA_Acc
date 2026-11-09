"""Frozen resource-frequency primary/ablation, three train-only development folds."""
import json,sys,time
from pathlib import Path
from array import array
from collections import Counter
from resource_occupancy_frequency_v1 import fit,predict,SCALE
from maximum_weight_NET_closure_v1 import solve,verify
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]


def write(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2)


def main():
    pp=R/'experiments/mmc_resource_probability_development_protocol_v1_2026-10-19/protocol.json';plan=json.loads(pp.read_text());out=R/'experiments/mmc_resource_probability_development_v1_2026-10-19';out.mkdir(exist_ok=False);context=R/'experiments/mmc_resource_context_v1_2026-10-19';domain=json.loads((context/'domain.json').read_text());assert domain['byteorder']==sys.byteorder
    nodes=array('I');nodes.frombytes((context/'CHANNEL_ids.u32').read_bytes());assert len(nodes)==258720;channel=set(nodes);proof=context/'independent_verification_v1.json';pv=json.loads(proof.read_text());assert pv['status']=='ALL3_776160_CONTEXT_CODES_DOMAIN_AND_ORIGINAL_PREFIX_N_OCCUPANCIES_VERIFIED';core=R/'experiments/resource_occupancy_frequency_contract_v1_2026-10-19/verification.json';cv=json.loads(core.read_text());assert cv['status']=='EXACT_PROBABILITY_QUANTIZATION_PREFIX_PROJECTION_AND_TRAIN_ONLY_FREQUENCY_PASS' and all(sha(p)==h for p,h in cv['bindings'].items())
    original=R/'experiments/mmc_complete_NET_candidate_choice_diagnostic_protocol_v1_2026-10-19/protocol.json';inputs=json.loads(original.read_text());items={x['case']:x for x in inputs['cases']};ownerroot=R/'experiments/mmc_candidate_ownership_implications_v1_2026-10-19';ownerplan=json.loads((R/'experiments/mmc_coupled_chooser_cost_and_data_scope_v1_2026-10-19/input_only_choice_protocol_v1.json').read_text());bindings={str(p):sha(p) for p in [pp,proof,core,original,Path(__file__).resolve(),R/'tools/resource_occupancy_frequency_v1.py',R/'tools/maximum_weight_NET_closure_v1.py']};rows=[]
    def codes(case):
        p=context/(case+'.u16');assert plan['bindings'][str(p)]==sha(p);bindings[str(p)]=sha(p);a=array('H');a.frombytes(p.read_bytes());assert len(a)==258720;return a
    def labels(case):
        p=Path(items[case]['native_label']);assert inputs['bindings'][str(p)]==sha(p);bindings[str(p)]=sha(p);ledger={int(n):v for n,v in json.loads(p.read_text())['node_occupancy'].items()};y=[ledger.get(n,0) for n in nodes];assert all(type(v) is int and v in [0,1] for v in y);return y
    for fold in plan['folds']:
        case=fold['evaluation_case'];begin=time.perf_counter();train=fold['training_cases'];train_codes={c:codes(c) for c in train};train_labels={c:labels(c) for c in train};model_directory=out/case;model_directory.mkdir();models={};fit_times={}
        for arm,with_prefix in [(plan['primary_arm'],True),(plan['ablation_arm'],False)]:
            directory=model_directory/arm;directory.mkdir();t=time.perf_counter();m=fit(train_codes,train_labels,train,case,with_prefix);fit_times[arm]=time.perf_counter()-t;m['training_bindings']={str(p):sha(p) for c in train for p in [context/(c+'.u16'),Path(items[c]['native_label'])]};m['training_resources']=sum(m['counts']);assert m['training_resources']==517440;models[arm]=m;write(directory/'model.json',m)
        # Both fold models now frozen; evaluation labels have not been opened
        # for either model. Only evaluation context and candidate inputs follow.
        del train_codes,train_labels;test=codes(case);gp=ownerroot/case/'graph.json';bp=ownerroot/case/'banks.jsonl'
        for p in [gp,bp]:assert ownerplan['bindings'][str(p)]==sha(p);bindings[str(p)]=sha(p)
        g=json.loads(gp.read_text());banks={x['net_id']:(set(x['A']),set(x['B'])) for x in map(json.loads,bp.open())};assert set(banks)==set(g['nodes']) and len(banks)==55300;A=Counter(n for a,b in banks.values() for n in a);B=Counter(n for a,b in banks.values() for n in b);safe={n for n in channel if A[n]<=1 and B[n]<=1}
        for arm,m in models.items():
            directory=model_directory/arm;t=time.perf_counter();probabilities=predict(m,test);coeff={n:SCALE-2*p for n,p in zip(nodes,probabilities) if n in safe};weights={net:sum(coeff[n] for n in (a-b)&safe)-sum(coeff[n] for n in (b-a)&safe) for net,(a,b) in banks.items()};encoded={n:55301*w-1 for n,w in weights.items()};groups=g['components'];cw={i:sum(encoded[n] for n in c) for i,c in enumerate(groups)};weight_seconds=time.perf_counter()-t;t=time.perf_counter();certificate=solve(cw,list(map(tuple,g['condensation_edges'])));verify(cw,list(map(tuple,g['condensation_edges'])),certificate);solve_seconds=time.perf_counter()-t;chosen={n for i in certificate['selected'] for n in groups[i]};assert all(e['source'] not in chosen or e['target'] in chosen for e in g['edges'])
            ledger=Counter(n for net,(a,b) in banks.items() for n in (b if net in chosen else a));assert all(ledger[n]<=1 for n in safe) and all(ledger[n]<=1 for n in g['eligible_resources']);gain=sum(weights[n] for n in chosen);assert certificate['objective']==55301*gain-len(chosen)
            cp=directory/'choices.jsonl'
            with cp.open('x') as f:
                for net in sorted(banks):f.write(json.dumps(dict(net_id=net,expected_gain_scaled=weights[net],encoded_weight=encoded[net],pick='B' if net in chosen else 'A'),separators=(',',':'))+'\n')
            probfile=directory/'probabilities.u32';probfile.write_bytes(array('I',probabilities).tobytes());write(directory/'flow_cut_certificate.json',certificate);write(directory/'ledger.json',dict(ledger));rows.append(dict(case=case,arm=arm,with_prefix=m['with_prefix'],training_cases=train,training_resources=m['training_resources'],B_NETs=len(chosen),actual_NET_ownership_changes=sum(banks[n][0]!=banks[n][1] for n in chosen),safe_CHANNELs=len(safe),excluded_CHANNELs=len(channel-safe),expected_safe_L1_gain_scaled=gain,fit_seconds=fit_times[arm],probability_and_weights_seconds=weight_seconds,solve_and_certificate_seconds=solve_seconds,heldout_labels_used_for_model=False,eligible_for_legal_route_commit=False))
            for p in [directory/'model.json',cp,probfile,directory/'flow_cut_certificate.json',directory/'ledger.json']:bindings[str(p)]=sha(p)
            print('RESOURCE_FREQUENCY_CLOSED_CHOICE',case,arm,'changed',rows[-1]['actual_NET_ownership_changes'],'B',len(chosen),flush=True)
    write(out/'receipt.json',dict(status='ALL6_FIXED_RESOURCE_FREQUENCY_FOLDS_AND_CLOSED_CHOICES_PRODUCED',rows=rows,bindings=bindings,primary_arm=plan['primary_arm'],ablation_arm=plan['ablation_arm'],quality_evaluation_executed=False,independent_verification_pending=True,scope=plan['scope']))


if __name__=='__main__':main()
