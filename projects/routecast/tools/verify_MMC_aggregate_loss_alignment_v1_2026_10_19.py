"""Independent resource-owner scatter weights and occupancy error histograms."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict,Counter
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]


def main():
    root=R/'experiments/mmc_aggregate_loss_alignment_v1_2026-10-19';rp=root/'review.json';d=json.loads(rp.read_text());assert all(sha(p)==h for p,h in d['bindings'].items())
    pp=R/'experiments/mmc_complete_NET_candidate_choice_diagnostic_protocol_v1_2026-10-19/protocol.json';plan=json.loads(pp.read_text());source=R/'experiments/mmc_candidate_ownership_implications_v1_2026-10-19';graph=next(Path(p) for p in d['bindings'] if p.endswith('rr_graph.xml'));channel=set();stack=[]
    for event,e in ET.iterparse(graph,events=('start','end')):
        if event=='start':stack.append(e);continue
        if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
            if e.get('type') in ['CHANX','CHANY'] and int(e.get('capacity'))>0:assert int(e.get('capacity'))==1;channel.add(int(e.get('id')))
            stack[-2].remove(e);e.clear()
        if e.tag=='rr_nodes':break
        stack.pop()
    oldproof=R/'experiments/mmc_coupled_ridge_labels_v1_2026-10-19/verification.json';oldv=json.loads(oldproof.read_text());verified=[]
    for item in plan['cases']:
        case=item['case'];row=next(x for x in d['rows'] if x['case']==case);banks={x['net_id']:x for x in map(json.loads,(source/case/'banks.jsonl').open())};owners=[defaultdict(set),defaultdict(set)]
        for net,b in banks.items():
            for i,key in enumerate(['A','B']):
                for node in b[key]:
                    if node in channel:owners[i][node].add(net)
        safe={node for node in channel if len(owners[0][node])<=1 and len(owners[1][node])<=1};assert len(safe)==row['safe_CHANNELs'] and len(channel-safe)==row['excluded_CHANNELs'];truth={int(n):v for n,v in json.loads(Path(item['native_label']).read_text())['node_occupancy'].items()};expected={net:0 for net in banks}
        for n in safe:
            assert truth.get(n,0) in [0,1];sign=1-2*truth.get(n,0)
            for net in owners[0][n]:expected[net]+=sign
            for net in owners[1][n]:expected[net]-=sign
        actual={x['net_id']:x['y'] for x in map(json.loads,(root/(case+'.aggregate_labels.jsonl')).open())};assert expected==actual
        oldpath=R/'experiments/mmc_coupled_ridge_labels_v1_2026-10-19'/(case+'.jsonl');assert oldv['bindings'][str(oldpath)]==sha(oldpath);old={x['net_id']:x['y'] for x in map(json.loads,oldpath.open())};assert set(old)==set(expected)
        assert sum(old[n]!=actual[n] for n in actual)==row['labels_different_from_owner_surrogate'] and sum(old[n]*actual[n]<0 for n in actual)==row['opposite_nonzero_label_signs']
        maskpaths={'independent_label_guided':'mmc_complete_NET_choice_diagnostic_v1_2026-10-19','fixed_input_score':'mmc_input_only_closed_choice_v1_2026-10-19','ridge_development':'mmc_coupled_ridge_development_v1_2026-10-19'}
        mainreview=json.loads((source/'review.json').read_text());closed=next(c for x in mainreview['rows'] if x['case']==case for c in x['closure_checks'] if c['seed']=='archived_label_guided_diagnostic')
        for check in row['choices']:
            name=check['choice']
            if name=='all_A':chosen=set()
            elif name=='all_B':chosen=set(banks)
            elif name=='dependency_closed_label_guided':chosen=set(closed['closed_B_NET_ids'])
            else:chosen={x['net_id'] for x in map(json.loads,(R/'experiments'/maskpaths[name]/case/'choices.jsonl').open()) if x['pick']=='B'}
            histogram=Counter();excluded_error=0;direct_before=0
            for n in channel:
                count=len(owners[0][n]-chosen)+len(owners[1][n]&chosen);t=truth.get(n,0)
                if n in safe:histogram[len(owners[0][n]),count,t]+=1
                else:excluded_error+=abs(count-t)
            baseline=sum(k*abs(a-t) for (a,c,t),k in histogram.items());after=sum(k*abs(c-t) for (a,c,t),k in histogram.items());direct=baseline-after;linear=sum(actual[n] for n in chosen);over=sum(k for (a,c,t),k in histogram.items() if c>1)
            # Binary truth gives an exact correction even for the deliberately
            # unclosed diagnostic mask; overuse with truth0 need not break it.
            correction=2*sum(k*max(0,c-1)*t for (a,c,t),k in histogram.items());assert linear-direct==correction
            assert baseline==row['baseline_safe_L1'] and direct==check['direct_safe_L1_improvement'] and linear==check['linear_weight_sum'] and over==check['safe_overused_resources'] and excluded_error==check['excluded_domain_L1']
            assert check['identity_holds']==(correction==0)
        verified.append(dict(case=case,NETs=len(actual),safe_CHANNELs=len(safe),archived_masks=len(row['choices'])));print('AGGREGATE_RESOURCE_SCATTER_AND_ERROR_HISTOGRAMS_PASS',case,flush=True)
    with (root/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='ALL3_AGGREGATE_LABELS_SAFE_EXCLUSIONS_AND_EIGHTEEN_MASK_HISTOGRAM_IDENTITIES_VERIFIED',rows=verified,bindings={str(p):sha(p) for p in [rp,Path(__file__).resolve(),oldproof]},scope='Independent resource-wise scatter and histogram accounting, including exact nonclosed-mask correction. Label-only diagnostic; no new predictor or full quality/optimality claim.'),f,indent=2)


if __name__=='__main__':main()
