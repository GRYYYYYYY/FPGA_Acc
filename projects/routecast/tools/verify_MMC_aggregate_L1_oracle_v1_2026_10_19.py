"""Independent true-occupancy scatter labels, feasible flow/cut and exact losses."""
import json,xml.parsers.expat as expat
from pathlib import Path
from array import array
from collections import Counter,defaultdict
from pre_route_endpoints import sha
from maximum_weight_NET_closure_v1 import verify

R=Path(__file__).resolve().parents[1]


def main():
    root=R/'experiments/mmc_aggregate_L1_oracle_v1_2026-10-19';rp=root/'receipt.json';d=json.loads(rp.read_text());assert d['target_labels_read'] is True and all(sha(p)==h for p,h in d['bindings'].items())
    pp=R/'experiments/mmc_complete_NET_candidate_choice_diagnostic_protocol_v1_2026-10-19/protocol.json';plan=json.loads(pp.read_text());inputprotocol=R/'experiments/mmc_coupled_chooser_cost_and_data_scope_v1_2026-10-19/input_only_choice_protocol_v1.json';pinned=json.loads(inputprotocol.read_text());source=R/'experiments/mmc_candidate_ownership_implications_v1_2026-10-19';graph=next(Path(p) for p in d['bindings'] if p.endswith('rr_graph.xml'));caps=array('I');channel=set();stack=[]
    class Done(Exception):pass
    def opening(tag,a):
        if tag=='node' and stack and stack[-1]=='rr_nodes':
            n=int(a['id']);caps.append(int(a['capacity']))
            if a['type'] in ['CHANX','CHANY'] and caps[n]>0:assert caps[n]==1;channel.add(n)
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
    for item in plan['cases']:
        case=item['case'];row=next(x for x in d['rows'] if x['case']==case);gp=source/case/'graph.json';bp=source/case/'banks.jsonl'
        for p in [gp,bp]:assert pinned['bindings'][str(p)]==sha(p)==d['bindings'][str(p)]
        g=json.loads(gp.read_text());banks={x['net_id']:x for x in map(json.loads,bp.open())};assert set(banks)==set(g['nodes']) and len(banks)==55300;A=Counter();B=Counter();owners=[defaultdict(set),defaultdict(set)]
        for net,x in banks.items():
            A.update(x['A']);B.update(x['B'])
            for i,key in enumerate(['A','B']):
                for n in x[key]:
                    if n in channel:owners[i][n].add(net)
        safe={n for n in channel if len(owners[0][n])<=1 and len(owners[1][n])<=1};target=Path(item['native_label']);assert plan['bindings'][str(target)]==sha(target);truth={int(n):v for n,v in json.loads(target.read_text())['node_occupancy'].items()};weight={n:0 for n in banks}
        for n in safe:
            t=truth.get(n,0);assert t in [0,1]
            for net in owners[0][n]:weight[net]+=1-2*t
            for net in owners[1][n]:weight[net]-=1-2*t
        choices={x['net_id']:x for x in map(json.loads,(root/case/'choices.jsonl').open())};assert set(choices)==set(banks);selected=set()
        for net,w in weight.items():
            choice=choices[net];assert choice['aggregate_gain']==w and choice['encoded_weight']==55301*w-1 and choice['pick'] in ['A','B']
            if choice['pick']=='B':selected.add(net)
        encoded={n:55301*w-1 for n,w in weight.items()};groups=g['components'];cw={i:sum(encoded[n] for n in c) for i,c in enumerate(groups)};cert=json.loads((root/case/'flow_cut_certificate.json').read_text());objective=verify(cw,list(map(tuple,g['condensation_edges'])),cert)
        assert selected=={n for i in cert['selected'] for n in groups[i]} and all(e['source'] not in selected or e['target'] in selected for e in g['edges'])
        ledger=A.copy()
        for net in selected:ledger.subtract(banks[net]['A']);ledger.update(banks[net]['B'])
        assert {n:v for n,v in ledger.items() if v}=={int(n):v for n,v in json.loads((root/case/'ledger.json').read_text()).items()}
        assert all(ledger[n]<=1 for n in safe) and all(ledger[n]<=1 for n in g['eligible_resources'])
        before=sum(abs(A[n]-truth.get(n,0)) for n in safe);after=sum(abs(ledger[n]-truth.get(n,0)) for n in safe);gain=sum(weight[n] for n in selected);excluded=sum(abs(ledger[n]-truth.get(n,0)) for n in channel-safe)
        assert before-after==gain==row['safe_L1_gain'] and objective==55301*gain-len(selected)
        assert (before,after,len(safe),len(channel-safe),excluded,after+excluded)==tuple(row[k] for k in ['baseline_safe_L1','chosen_safe_L1','safe_CHANNELs','excluded_CHANNELs','excluded_L1','full_CHANNEL_L1'])
        assert len(selected)==row['B_NETs'] and sum(max(0,v-caps[n]) for n,v in ledger.items())==row['overflow_units']
        rows.append(dict(case=case,NETs=55300,exact_safe_L1_gain=gain,excluded_L1=excluded));print('AGGREGATE_L1_ORACLE_SCATTER_CUT_AND_DIRECT_LOSS_PASS',case,flush=True)
    with (root/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='ALL3_AGGREGATE_ORACLE_WEIGHTS_BANK_BINDINGS_FLOWCUT_AND_DIRECT_LOSSES_VERIFIED',rows=rows,bindings={str(p):sha(p) for p in [rp,inputprotocol,Path(__file__).resolve()]},scope='Target-using exact safe-domain L1 optimum over fixed bank graph only. Pinned bank membership inherits prior full physical proof; no Spearman/topK optimality or deployable predictor claim.'),f,indent=2)


if __name__=='__main__':main()
