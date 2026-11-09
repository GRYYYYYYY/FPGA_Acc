"""Exact safe-domain aggregate L1 targets; retrospective accounting, no fitting."""
import json,xml.parsers.expat as expat
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]


def main():
    out=R/'experiments/mmc_aggregate_loss_alignment_v1_2026-10-19';out.mkdir(exist_ok=False)
    pp=R/'experiments/mmc_complete_NET_candidate_choice_diagnostic_protocol_v1_2026-10-19/protocol.json';plan=json.loads(pp.read_text());source=R/'experiments/mmc_candidate_ownership_implications_v1_2026-10-19';proof=source/'independent_verification_v1.json';pv=json.loads(proof.read_text());assert pv['status']=='ALL3_ORIGINAL_BANKS_COMPLETE_IMPLICATIONS_SCC_AND_TWELVE_CLOSURES_VERIFIED'
    graph=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/rr/mmc/rr_graph.xml';channel=set();stack=[]
    class Done(Exception):pass
    def opening(tag,a):
        if tag=='node' and stack and stack[-1]=='rr_nodes' and a['type'] in ['CHANX','CHANY'] and int(a['capacity'])>0:
            assert int(a['capacity'])==1;channel.add(int(a['id']))
        stack.append(tag)
    def closing(tag):
        assert stack.pop()==tag
        if tag=='rr_nodes':raise Done()
    parser=expat.ParserCreate();parser.StartElementHandler=opening;parser.EndElementHandler=closing
    try:
        with graph.open('rb') as f:
            for b in iter(lambda:f.read(1<<20),b''):parser.Parse(b,False)
    except Done:pass
    assert len(channel)==258720
    bindings={str(p):sha(p) for p in [pp,proof,graph,Path(__file__).resolve()]};rows=[]
    reviewpath=source/'review.json';assert pv['bindings'][str(reviewpath)]==sha(reviewpath);review=json.loads(reviewpath.read_text());bindings[str(reviewpath)]=sha(reviewpath)
    for item in plan['cases']:
        case=item['case'];bankpath=source/case/'banks.jsonl';assert review['bindings'][str(bankpath)]==sha(bankpath);banks={x['net_id']:(set(x['A'])&channel,set(x['B'])&channel) for x in map(json.loads,bankpath.open())};assert len(banks)==55300
        A=Counter(n for a,b in banks.values() for n in a);B=Counter(n for a,b in banks.values() for n in b);safe={n for n in channel if A[n]<=1 and B[n]<=1};excluded=channel-safe
        target=Path(item['native_label']);assert plan['bindings'][str(target)]==sha(target);native={int(n):v for n,v in json.loads(target.read_text())['node_occupancy'].items()};assert all(native.get(n,0) in [0,1] for n in channel)
        coefficient={n:1-2*native.get(n,0) for n in safe};weights={net:sum(coefficient[n] for n in a&safe)-sum(coefficient[n] for n in b&safe) for net,(a,b) in banks.items()};baseline=sum(abs(A[n]-native.get(n,0)) for n in safe)
        labelpath=out/(case+'.aggregate_labels.jsonl')
        with labelpath.open('x') as f:
            for net in sorted(weights):f.write(json.dumps(dict(net_id=net,y=weights[net]),separators=(',',':'))+'\n')
        oldlabels=R/'experiments/mmc_coupled_ridge_labels_v1_2026-10-19'/(case+'.jsonl');old={x['net_id']:x['y'] for x in map(json.loads,oldlabels.open())};assert set(old)==set(weights);opposite=sum(old[n]*weights[n]<0 for n in weights);different=sum(old[n]!=weights[n] for n in weights)
        masks={'all_A':set(),'all_B':set(banks)};maskpaths=[]
        for name,directory in [('independent_label_guided','mmc_complete_NET_choice_diagnostic_v1_2026-10-19'),('fixed_input_score','mmc_input_only_closed_choice_v1_2026-10-19'),('ridge_development','mmc_coupled_ridge_development_v1_2026-10-19')]:
            path=R/'experiments'/directory/case/'choices.jsonl';masks[name]={x['net_id'] for x in map(json.loads,path.open()) if x['pick']=='B'};maskpaths.append(path)
        original_row=next(x for x in review['rows'] if x['case']==case);closed=next(x for x in original_row['closure_checks'] if x['seed']=='archived_label_guided_diagnostic');masks['dependency_closed_label_guided']=set(closed['closed_B_NET_ids']);checks=[]
        for name,chosen in masks.items():
            occupancy=Counter(n for net,(a,b) in banks.items() for n in (b if net in chosen else a));over=sum(occupancy[n]>1 for n in safe);direct=baseline-sum(abs(occupancy[n]-native.get(n,0)) for n in safe);linear=sum(weights[n] for n in chosen)
            if not over:assert direct==linear
            else:assert direct!=linear
            checks.append(dict(choice=name,B_NETs=len(chosen),safe_overused_resources=over,direct_safe_L1_improvement=direct,linear_weight_sum=linear,identity_holds=direct==linear,excluded_domain_L1=sum(abs(occupancy[n]-native.get(n,0)) for n in excluded)))
        rows.append(dict(case=case,CHANNELs=len(channel),safe_CHANNELs=len(safe),excluded_CHANNELs=len(excluded),baseline_safe_L1=baseline,labels_different_from_owner_surrogate=different,opposite_nonzero_label_signs=opposite,choices=checks))
        bindings.update({str(p):sha(p) for p in [bankpath,target,oldlabels,labelpath,*maskpaths]});print('AGGREGATE_LOSS_ALIGNMENT',case,'safe',len(safe),'excluded',len(excluded),'different_labels',different,'opposite',opposite,flush=True)
    (out/'review.json').write_text(json.dumps(dict(status='ALL3_AGGREGATE_SAFE_DOMAIN_LABELS_AND_SIX_ARCHIVED_CHOICE_ACCOUNTINGS_PRODUCED',rows=rows,bindings=bindings,scope='Retrospective target-only loss diagnosis, no new inference or fitting. Exact L1 identity only on binary safe CHANNEL domain; excluded error reported. L1 does not replace original Spearman/topK gates or imply quality upper bounds.',independent_verification_pending=True),indent=2)+'\n')


if __name__=='__main__':main()
