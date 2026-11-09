"""Target-using aggregate-loss oracle, never an inference predictor."""
import json,time,xml.parsers.expat as expat
from pathlib import Path
from array import array
from collections import Counter
from maximum_weight_NET_closure_v1 import solve,verify
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]


def save(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2)


def main():
    pp=R/'experiments/mmc_aggregate_L1_oracle_protocol_v1_2026-10-19/protocol.json';plan=json.loads(pp.read_text());assert all(sha(p)==h for p,h in plan['bindings'].items());out=R/'experiments/mmc_aggregate_L1_oracle_v1_2026-10-19';out.mkdir(exist_ok=False)
    alignment=R/'experiments/mmc_aggregate_loss_alignment_v1_2026-10-19';ar=alignment/'review.json';av=alignment/'independent_verification_v1.json';audit=json.loads(ar.read_text());proof=json.loads(av.read_text());assert proof['status']=='ALL3_AGGREGATE_LABELS_SAFE_EXCLUSIONS_AND_EIGHTEEN_MASK_HISTOGRAM_IDENTITIES_VERIFIED' and proof['bindings'][str(ar)]==sha(ar)
    original=R/'experiments/mmc_complete_NET_candidate_choice_diagnostic_protocol_v1_2026-10-19/protocol.json';inputs=json.loads(original.read_text());source=R/'experiments/mmc_candidate_ownership_implications_v1_2026-10-19';bindings={str(p):sha(p) for p in [pp,ar,av,original,Path(__file__).resolve(),R/'tools/maximum_weight_NET_closure_v1.py']}
    graph=next(Path(p) for p in audit['bindings'] if p.endswith('rr_graph.xml'));assert audit['bindings'][str(graph)]==sha(graph);caps=array('I');channel=set();stack=[]
    class Done(Exception):pass
    def opening(tag,a):
        if tag=='node' and stack and stack[-1]=='rr_nodes':
            n=int(a['id']);assert n==len(caps);caps.append(int(a['capacity']))
            if caps[n]>0 and a['type'] in ['CHANX','CHANY']:assert caps[n]==1;channel.add(n)
        stack.append(tag)
    def closing(tag):
        assert stack.pop()==tag
        if tag=='rr_nodes':raise Done()
    parser=expat.ParserCreate();parser.StartElementHandler=opening;parser.EndElementHandler=closing
    try:
        with graph.open('rb') as f:
            for b in iter(lambda:f.read(1<<20),b''):parser.Parse(b,False)
    except Done:pass
    assert len(caps)==904438 and len(channel)==258720;bindings[str(graph)]=sha(graph);rows=[]
    for item in inputs['cases']:
        case=item['case'];directory=out/case;directory.mkdir();gp=source/case/'graph.json';bp=source/case/'banks.jsonl';assert audit['bindings'][str(bp)]==sha(bp);g=json.loads(gp.read_text());bank={x['net_id']:x for x in map(json.loads,bp.open())};N=len(g['nodes']);assert set(bank)==set(g['nodes']) and N==55300
        lp=alignment/(case+'.aggregate_labels.jsonl');assert plan['bindings'][str(lp)]==sha(lp);weights={x['net_id']:x['y'] for x in map(json.loads,lp.open())};assert set(weights)==set(bank) and all(type(x) is int for x in weights.values());encoded={n:(N+1)*w-1 for n,w in weights.items()};groups=g['components'];cw={i:sum(encoded[n] for n in c) for i,c in enumerate(groups)}
        tick=time.perf_counter();cert=solve(cw,list(map(tuple,g['condensation_edges'])));verify(cw,list(map(tuple,g['condensation_edges'])),cert);seconds=time.perf_counter()-tick;chosen={n for i in cert['selected'] for n in groups[i]};assert all(e['source'] not in chosen or e['target'] in chosen for e in g['edges'])
        A=Counter(n for b in bank.values() for n in b['A']);B=Counter(n for b in bank.values() for n in b['B']);safe={n for n in channel if A[n]<=1 and B[n]<=1};excluded=channel-safe;ledger=Counter(n for net,b in bank.items() for n in b['B' if net in chosen else 'A']);assert all(ledger[n]<=1 for n in safe)
        label=Path(item['native_label']);assert audit['bindings'][str(label)]==sha(label);truth={int(n):v for n,v in json.loads(label.read_text())['node_occupancy'].items()};baseline=sum(abs(A[n]-truth.get(n,0)) for n in safe);after=sum(abs(ledger[n]-truth.get(n,0)) for n in safe);gain=sum(weights[n] for n in chosen)
        assert baseline-after==gain and cert['objective']==(N+1)*gain-len(chosen);ref=next(x for x in audit['rows'] if x['case']==case);assert baseline==ref['baseline_safe_L1'] and len(excluded)==ref['excluded_CHANNELs']
        excluded_error=sum(abs(ledger[n]-truth.get(n,0)) for n in excluded);overflow=sum(max(0,v-caps[n]) for n,v in ledger.items());cp=directory/'choices.jsonl'
        with cp.open('x') as f:
            for net in sorted(bank):f.write(json.dumps(dict(net_id=net,aggregate_gain=weights[net],encoded_weight=encoded[net],pick='B' if net in chosen else 'A'),separators=(',',':'))+'\n')
        save(directory/'flow_cut_certificate.json',cert);save(directory/'ledger.json',dict(ledger));rows.append(dict(case=case,B_NETs=len(chosen),safe_CHANNELs=len(safe),excluded_CHANNELs=len(excluded),baseline_safe_L1=baseline,chosen_safe_L1=after,safe_L1_gain=gain,excluded_L1=excluded_error,full_CHANNEL_L1=after+excluded_error,overflow_units=overflow,solver_and_certificate_seconds=seconds,eligible_for_legal_route_commit=False))
        bindings.update({str(p):sha(p) for p in [gp,bp,lp,label,cp,directory/'flow_cut_certificate.json',directory/'ledger.json']});print('AGGREGATE_L1_ORACLE',case,'B',len(chosen),'safe_gain',gain,'excluded_error',excluded_error,'overflow',overflow,flush=True)
    save(out/'receipt.json',dict(status='ALL3_TARGET_USING_AGGREGATE_L1_ORACLE_CHOICES_PRODUCED',rows=rows,bindings=bindings,target_labels_read=True,independent_verification_pending=True,scope=plan['scope']))


if __name__=='__main__':main()
