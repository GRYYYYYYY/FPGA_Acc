"""Independently rebuild scores and ledger; verify flow/cut without optimizing."""
import json,xml.parsers.expat as expat
from pathlib import Path
from array import array
from collections import Counter
from maximum_weight_NET_closure_v1 import verify
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]


def main():
    root=R/'experiments/mmc_input_only_closed_choice_v1_2026-10-19';rp=root/'receipt.json';d=json.loads(rp.read_text());assert d['status']=='ALL3_INPUT_ONLY_FIXED_SCORE_CLOSED_CHOICES_PRODUCED' and d['target_labels_read'] is False
    assert all(sha(p)==h for p,h in d['bindings'].items());source=R/'experiments/mmc_candidate_ownership_implications_v1_2026-10-19';graph=next(Path(p) for p in d['bindings'] if p.endswith('rr_graph.xml'));caps=array('I');channel=set();stack=[]
    class Done(Exception):pass
    def opening(tag,a):
        if tag=='node' and stack and stack[-1]=='rr_nodes':
            n=int(a['id']);assert n==len(caps);caps.append(int(a['capacity']))
            if caps[n]>0 and a['type'] in ['CHANX','CHANY']:channel.add(n)
        stack.append(tag)
    def closing(tag):
        assert stack.pop()==tag
        if tag=='rr_nodes':raise Done()
    parser=expat.ParserCreate();parser.StartElementHandler=opening;parser.EndElementHandler=closing
    try:
        with graph.open('rb') as f:
            for b in iter(lambda:f.read(1<<20),b''):parser.Parse(b,False)
    except Done:pass
    assert len(caps)==904438 and len(channel)==258720;rows=[]
    for row in d['rows']:
        case=row['case'];g=json.loads((source/case/'graph.json').read_text());N=len(g['nodes']);choices={x['net_id']:x for x in map(json.loads,(root/case/'choices.jsonl').open())};assert len(choices)==N==55300
        weights={};ledger=Counter();selected=set();gain=0;seen=set()
        for x in map(json.loads,(source/case/'banks.jsonl').open()):
            net=x['net_id'];assert net not in seen;seen.add(net);a,b=set(x['A']),set(x['B']);na,nb=len(a&channel),len(b&channel);choice=choices[net]
            assert (choice['A_CHANNELs'],choice['B_CHANNELs'],choice['gain'],choice['encoded'])==(na,nb,na-nb,(N+1)*(na-nb)-1)
            weights[net]=choice['encoded'];ledger.update(a)
            assert choice['pick'] in ['A','B']
            if choice['pick']=='B':selected.add(net);gain+=na-nb;ledger.subtract(a-b);ledger.update(b-a)
        assert seen==set(g['nodes'])==set(choices);groups=g['components'];cw={i:sum(weights[n] for n in group) for i,group in enumerate(groups)};certificate=json.loads((root/case/'flow_cut_certificate.json').read_text());optimum=verify(cw,list(map(tuple,g['condensation_edges'])),certificate)
        assert {n for i in certificate['selected'] for n in groups[i]}==selected
        assert all(e['source'] not in selected or e['target'] in selected for e in g['edges'])
        assert optimum==(N+1)*gain-len(selected)==row['encoded_objective']
        assert gain==row['CHANNEL_demand_reduction'] and len(selected)==row['B_NETs']
        positive={n:v for n,v in ledger.items() if v};stored={int(n):v for n,v in json.loads((root/case/'ledger.json').read_text()).items()};assert positive==stored and all(v>0 for v in positive.values())
        assert all(ledger[n]<=1 for n in g['eligible_resources']) and row['protected_domain_overflow']==0
        assert sum(max(0,v-caps[n]) for n,v in positive.items())==row['overflow_units'] and row['eligible_for_legal_route_commit'] is False
        rows.append(dict(case=case,NETs=N,exact_encoded_objective=optimum));print('INPUT_ONLY_SCORES_MINCUT_AND_LEDGER_INDEPENDENT_PASS',case,flush=True)
    with (root/'independent_verification_v1.json').open('x') as f:
        json.dump(dict(status='ALL3_INPUT_ONLY_SCORES_EXACT_FLOW_CUT_OPTIMA_AND_LEDGER_VERIFIED',rows=rows,bindings={str(p):sha(p) for p in [rp,Path(__file__).resolve(),R/'tools/maximum_weight_NET_closure_v1.py']},scope='Separate input-only score/ledger construction and feasible flow/cut equality; no optimization rerun and no target labels. Existing physical bank proofs inherited. No full capacity legalization or forecast quality claim.'),f,indent=2)


if __name__=='__main__':main()
